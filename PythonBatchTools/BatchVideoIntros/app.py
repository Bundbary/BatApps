import json
import win32com.client
import os
import time
import pythoncom
import threading
import win32gui
import win32con

def read_video_info(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    video_stream = next(s for s in data['streams'] if s['codec_type'] == 'video')
    
    return {
        'width': video_stream['width'],
        'height': video_stream['height'],
        'frame_rate': eval(video_stream['r_frame_rate']),
        'codec': video_stream['codec_name'],
        'pix_fmt': video_stream['pix_fmt'],
        'color_space': video_stream['color_space'],
        'color_transfer': video_stream['color_transfer'],
        'color_primaries': video_stream['color_primaries']
    }

def minimize_powerpoint(powerpoint):
    time.sleep(1)
    hwnd = win32gui.FindWindow(None, "PowerPoint")
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)

def create_presentation(title, subtitle, timestamps, video_info):
    pythoncom.CoInitialize()
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = True
    try:
        threading.Thread(target=minimize_powerpoint, args=(powerpoint,), daemon=True).start()

        presentation = powerpoint.Presentations.Add()
        
        # Set slide size to match video dimensions
        presentation.PageSetup.SlideWidth = video_info['width']
        presentation.PageSetup.SlideHeight = video_info['height']

        slide = presentation.Slides.Add(1, 12)  # 12 corresponds to ppLayoutBlank

        # Set background color to white
        slide.Background.Fill.ForeColor.RGB = 255 + 255*256 + 255*256*256

        # Add title
        title_box = slide.Shapes.AddTextbox(1, 30, 30, video_info['width'] - 60, 50)
        title_box.TextFrame.TextRange.Text = title
        title_box.TextFrame.TextRange.Font.Name = "Arial"
        title_box.TextFrame.TextRange.Font.Size = 32
        title_box.TextFrame.TextRange.Font.Color.RGB = 255 + 0*256 + 147*256*256  # Hot pink
        title_box.TextFrame.TextRange.ParagraphFormat.Alignment = 1  # 1 corresponds to ppAlignLeft

        # Add subtitle
        subtitle_box = slide.Shapes.AddTextbox(1, 30, 90, video_info['width'] - 60, 60)
        subtitle_box.TextFrame.TextRange.Text = subtitle
        subtitle_box.TextFrame.TextRange.Font.Name = "Arial"
        subtitle_box.TextFrame.TextRange.Font.Size = 16
        subtitle_box.TextFrame.TextRange.Font.Color.RGB = 0  # Black
        subtitle_box.TextFrame.TextRange.ParagraphFormat.Alignment = 1

        # Add timestamps
        timestamp_boxes = []
        for i, timestamp in enumerate(timestamps):
            ts_box = slide.Shapes.AddTextbox(1, 30, 180 + i*30, video_info['width'] - 60, 25)
            ts_box.TextFrame.TextRange.Text = timestamp
            ts_box.TextFrame.TextRange.Font.Name = "Consolas"
            ts_box.TextFrame.TextRange.Font.Size = 14
            ts_box.TextFrame.TextRange.Font.Color.RGB = 0  # Black
            ts_box.TextFrame.TextRange.ParagraphFormat.Alignment = 1
            timestamp_boxes.append(ts_box)

        # Add placeholder for image
        img_placeholder = slide.Shapes.AddShape(1, video_info['width'] - 580, 30, 550, 400)  # 1 corresponds to msoShapeRectangle
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
        title_box.AnimationSettings.TextLevelEffect = 0
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

def export_to_video(presentation, video_path, video_info):
    try:
        # Use video_info to set export parameters
        frame_rate = min(30, video_info['frame_rate'])  # PowerPoint max is 30 fps
        quality = 95  # Assuming high quality, adjust if needed
        
        presentation.CreateVideo(video_path, -1, 15, video_info['height'], frame_rate, quality)
        print(f"Video export initiated. File will be saved to: {video_path}")
        
        # Wait for the file to be created and fully written
        max_wait_time = 300  # 5 minutes
        start_time = time.time()
        last_size = -1
        
        while True:
            if os.path.exists(video_path):
                current_size = os.path.getsize(video_path)
                if current_size > 0 and current_size == last_size:
                    print(f"Video file created and fully written at: {video_path}")
                    break
                last_size = current_size
            
            if time.time() - start_time > max_wait_time:
                raise TimeoutError("Video export timed out after 5 minutes")
            
            time.sleep(1)  # Check every second
        
    except Exception as e:
        print(f"An error occurred during video export: {str(e)}")
        raise
    
def main(json_file_path):
    video_info = read_video_info(json_file_path)

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
        powerpoint, presentation, slide, title_box, subtitle_box, timestamp_boxes, img_placeholder = create_presentation(title, subtitle, timestamps, video_info)
        add_animations(slide, title_box, subtitle_box, timestamp_boxes, img_placeholder)

        pptx_path = os.path.abspath('intro_test_refined.pptx')
        presentation.SaveAs(pptx_path)
        print(f"Presentation saved to: {pptx_path}")

        video_path = os.path.abspath('intro_test_video_refined.mp4')
        export_to_video(presentation, video_path, video_info)

    except Exception as e:
        print(f"An error occurred: {str(e)}")
    
    finally:
        if powerpoint:
            powerpoint.Quit()
            pythoncom.CoUninitialize()

    print("Script completed.")

if __name__ == "__main__":
    json_file_path = 'video_info.json'  # You can change this to accept command line arguments if needed
    main(json_file_path)