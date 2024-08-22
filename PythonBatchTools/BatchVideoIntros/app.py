import win32com.client
import os
import time
import pythoncom

def create_presentation(title, subtitle, timestamps):
    pythoncom.CoInitialize()
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = True  # Make PowerPoint visible
    try:
        presentation = powerpoint.Presentations.Add()
        
        # Set slide size to 16:9 (widescreen)
        presentation.PageSetup.SlideSize = 4  # 4 corresponds to ppSlideSize16x9

        # Add a blank slide
        slide = presentation.Slides.Add(1, 12)  # 12 corresponds to ppLayoutBlank

        # Set background color to white
        slide.Background.Fill.ForeColor.RGB = 255 + 255*256 + 255*256*256

        # Add title
        title_box = slide.Shapes.AddTextbox(1, 30, 30, 640, 50)  # 1 corresponds to msoTextOrientationHorizontal
        title_box.TextFrame.TextRange.Text = title
        title_box.TextFrame.TextRange.Font.Name = "Arial"
        title_box.TextFrame.TextRange.Font.Size = 32
        title_box.TextFrame.TextRange.Font.Color.RGB = 255 + 0*256 + 147*256*256  # Hot pink
        title_box.TextFrame.TextRange.ParagraphFormat.Alignment = 1  # 1 corresponds to ppAlignLeft

        # Add subtitle
        subtitle_box = slide.Shapes.AddTextbox(1, 30, 90, 640, 60)
        subtitle_box.TextFrame.TextRange.Text = subtitle
        subtitle_box.TextFrame.TextRange.Font.Name = "Arial"
        subtitle_box.TextFrame.TextRange.Font.Size = 16
        subtitle_box.TextFrame.TextRange.Font.Color.RGB = 0  # Black
        subtitle_box.TextFrame.TextRange.ParagraphFormat.Alignment = 1

        # Add timestamps
        timestamp_boxes = []
        for i, timestamp in enumerate(timestamps):
            ts_box = slide.Shapes.AddTextbox(1, 30, 180 + i*30, 640, 25)
            ts_box.TextFrame.TextRange.Text = timestamp
            ts_box.TextFrame.TextRange.Font.Name = "Consolas"
            ts_box.TextFrame.TextRange.Font.Size = 14
            ts_box.TextFrame.TextRange.Font.Color.RGB = 0  # Black
            ts_box.TextFrame.TextRange.ParagraphFormat.Alignment = 1
            timestamp_boxes.append(ts_box)

        # Add placeholder for image
        img_placeholder = slide.Shapes.AddShape(1, 700, 30, 550, 400)  # 1 corresponds to msoShapeRectangle
        img_placeholder.Fill.ForeColor.RGB = 200 + 200*256 + 200*256*256  # Light gray

        return powerpoint, presentation, slide, title_box, subtitle_box, timestamp_boxes, img_placeholder
    except Exception as e:
        print(f"An error occurred while creating the presentation: {str(e)}")
        if powerpoint:
            powerpoint.Quit()
        pythoncom.CoUninitialize()
        raise

def add_animations(slide, title_box, subtitle_box, timestamp_boxes, img_placeholder):
    try:
        # Add fade in animation to title
        title_box.AnimationSettings.TextLevelEffect = 0  # 0 corresponds to ppAnimateByAllLevels
        title_box.AnimationSettings.EntryEffect = 3844  # 3844 corresponds to ppEffectFlyFromLeft

        # Add fade in animation to subtitle
        subtitle_box.AnimationSettings.TextLevelEffect = 0
        subtitle_box.AnimationSettings.EntryEffect = 3844

        # Add appear animation to timestamps, one by one
        for ts_box in timestamp_boxes:
            ts_box.AnimationSettings.TextLevelEffect = 0
            ts_box.AnimationSettings.EntryEffect = 3585  # 3585 corresponds to ppEffectAppear

        # Add fade in animation to image placeholder
        img_placeholder.AnimationSettings.TextLevelEffect = 0
        img_placeholder.AnimationSettings.EntryEffect = 3844
    except Exception as e:
        print(f"An error occurred while adding animations: {str(e)}")
        raise

def export_to_video(presentation, video_path):
    try:
        # Export to video
        presentation.CreateVideo(video_path)
        
        # Wait for the file to appear
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        while not os.path.exists(video_path):
            time.sleep(1)
            if time.time() - start_time > max_wait_time:
                print("Video export timed out. The file may not have been created.")
                return
        
        # Wait a bit longer to ensure the file is completely written
        time.sleep(10)
        
        print(f"Video exported successfully to: {video_path}")
    except Exception as e:
        print(f"An error occurred during video export: {str(e)}")
        raise

def main():
    # Sample data (you would normally load this from JSON)
    title = "VIDEO TITLE GOES IN THIS PLACE"
    subtitle = "Supporting text describing the video will go in this place. Maybe other general instructions."
    timestamps = [
        "Timestamp 1 . . . . . . . . . . . . . . . . . . . . . . . . . . . . 00:00",
        "Timestamp 2 . . . . . . . . . . . . . . . . . . . . . . . . . . . . 00:00",
        "Timestamp 3 . . . . . . . . . . . . . . . . . . . . . . . . . . . . 00:00",
        "Timestamp 4 . . . . . . . . . . . . . . . . . . . . . . . . . . . . 00:00",
        "Timestamp 5 . . . . . . . . . . . . . . . . . . . . . . . . . . . . 00:00"
    ]

    powerpoint = None
    try:
        # Create presentation and get references
        powerpoint, presentation, slide, title_box, subtitle_box, timestamp_boxes, img_placeholder = create_presentation(title, subtitle, timestamps)

        # Add animations
        add_animations(slide, title_box, subtitle_box, timestamp_boxes, img_placeholder)

        # Save the presentation
        pptx_path = os.path.abspath('intro_test_refined.pptx')
        presentation.SaveAs(pptx_path)
        print(f"Presentation saved to: {pptx_path}")

        # Export to video
        video_path = os.path.abspath('intro_test_video_refined.mp4')
        export_to_video(presentation, video_path)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        # Close PowerPoint
        if powerpoint:
            try:
                # print("Closing PowerPoint1...")
                # time.sleep(1)  # Add a 1-second delay before closing PowerPoint
                print("Closing PowerPoint2...")
                powerpoint.Quit()
            except Exception as e:
                print(f"Error while closing PowerPoint: {str(e)}")
        
        pythoncom.CoUninitialize()
    print("Script completed.")

if __name__ == "__main__":
    main()