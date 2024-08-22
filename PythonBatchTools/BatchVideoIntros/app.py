import json
import win32com.client
import os
import time
import pythoncom
import threading
import win32gui
import win32con


def read_video_info(json_file):
    with open(json_file, "r") as f:
        data = json.load(f)

    video_info = data["video"]
    video_info["frame_rate"] = eval(f"{video_info['frame_rate']}/1")  # Convert to float

    return {
        "video": video_info,
        "intro": data["intro"],
        "fonts": data["fonts"],
        "layout": data["layout"],
    }


def minimize_powerpoint(powerpoint):
    time.sleep(1)
    hwnd = win32gui.FindWindow(None, "PowerPoint")
    if hwnd:
        win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)


def create_presentation(video_info):
    pythoncom.CoInitialize()
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = True
    try:
        threading.Thread(
            target=minimize_powerpoint, args=(powerpoint,), daemon=True
        ).start()

        presentation = powerpoint.Presentations.Add()

        # Set slide size to match video dimensions
        presentation.PageSetup.SlideWidth = video_info["video"]["width"]
        presentation.PageSetup.SlideHeight = video_info["video"]["height"]

        slide = presentation.Slides.Add(1, 12)  # 12 corresponds to ppLayoutBlank

        # Set background color to white
        slide.Background.Fill.ForeColor.RGB = 255 + 255 * 256 + 255 * 256 * 256

        # Calculate dimensions
        margin = video_info["layout"]["margin"]
        padding = 50
        image_width = (
            video_info["video"]["width"]
            * video_info["layout"]["image_width_percentage"]
            / 100
        )
        text_width = video_info["video"]["width"] - image_width - margin - padding * 2

        # Add elements to the slide
        elements = []

        # Add image placeholder
        img_placeholder = slide.Shapes.AddShape(
            1,
            video_info["video"]["width"] - image_width,
            0,
            image_width,
            video_info["video"]["height"],
        )
        img_placeholder.Fill.ForeColor.RGB = (
            200 + 200 * 256 + 200 * 256 * 256
        )  # Light gray
        elements.append(img_placeholder)

        # Add title
        title_box = slide.Shapes.AddTextbox(
            1, margin + padding, margin + padding, text_width, 120
        )
        title_box.TextFrame.TextRange.Text = video_info["intro"]["title"]
        title_box.TextFrame.TextRange.ParagraphFormat.Alignment = (
            1  # 1 corresponds to ppAlignLeft
        )
        title_box.TextFrame.TextRange.Font.Name = video_info["fonts"]["title"]["name"]
        title_box.TextFrame.TextRange.Font.Size = video_info["fonts"]["title"]["size"]
        title_box.TextFrame.TextRange.Font.Color.RGB = int(
            video_info["fonts"]["title"]["color"].replace("#", "0x"), 16
        )
        elements.append(title_box)

        # Add subtitle
        subtitle_box = slide.Shapes.AddTextbox(
            1, margin + padding, margin + padding + 140, text_width, 60
        )
        subtitle_box.TextFrame.TextRange.Text = video_info["intro"]["subtitle"]
        subtitle_box.TextFrame.TextRange.ParagraphFormat.Alignment = 1
        subtitle_box.TextFrame.TextRange.Font.Name = video_info["fonts"]["subtitle"][
            "name"
        ]
        subtitle_box.TextFrame.TextRange.Font.Size = video_info["fonts"]["subtitle"][
            "size"
        ]
        subtitle_box.TextFrame.TextRange.Font.Color.RGB = int(
            video_info["fonts"]["subtitle"]["color"].replace("#", "0x"), 16
        )
        elements.append(subtitle_box)

        # Add timestamps
        for i, timestamp in enumerate(video_info["intro"]["timestamps"]):
            ts_box = slide.Shapes.AddTextbox(
                1, margin + padding, margin + padding + 220 + i * 40, text_width, 30
            )
            ts_box.TextFrame.TextRange.Text = timestamp
            ts_box.TextFrame.TextRange.ParagraphFormat.Alignment = 1
            ts_box.TextFrame.TextRange.Font.Name = video_info["fonts"]["timestamps"][
                "name"
            ]
            ts_box.TextFrame.TextRange.Font.Size = video_info["fonts"]["timestamps"][
                "size"
            ]
            ts_box.TextFrame.TextRange.Font.Color.RGB = int(
                video_info["fonts"]["timestamps"]["color"].replace("#", "0x"), 16
            )
            elements.append(ts_box)

        return powerpoint, presentation, slide, elements
    except Exception as e:
        print(f"An error occurred while creating the presentation: {str(e)}")
        if powerpoint:
            powerpoint.Quit()
        pythoncom.CoUninitialize()
        raise


msoAnimEffectFade = 14  # 14 is the value for msoAnimEffectFade
msoAnimTriggerOnPageClick = 1  # 1 is the value for msoAnimTriggerOnPageClick
msoAnimateLevelNone = 0  # 0 is the value for msoAnimateLevelNone
msoAnimTriggerWithPrevious = 2  # 2 is the value for msoAnimTriggerWithPrevious


import win32com.client

def add_animations(slide, elements):
    try:
        for i, element in enumerate(elements):
            # Add a fade effect to each element
            anim = slide.TimeLine.MainSequence.AddEffect(
                element,  # The shape to which the effect is applied
                14,  # msoAnimEffectFade (14)
                0,  # TextLevelEffect: msoAnimateLevelNone (0)
                1   # Trigger: msoAnimTriggerOnPageClick (1)
            )
            
            # Set the timing to start with previous (for smooth sequence)
            if i > 0:
                anim.Timing.TriggerType = 2  # msoAnimTriggerWithPrevious (2)
            
            # Add a small delay between animations
            anim.Timing.TriggerDelayTime = i * 0.5  # 0.5 second delay between each element
            
    except Exception as e:
        print(f"An error occurred while adding animations: {str(e)}")
        raise




def export_to_video(presentation, video_path, video_info):
    try:
        frame_rate = min(30, video_info["video"]["frame_rate"])
        quality = 95

        presentation.CreateVideo(
            video_path, -1, 15, video_info["video"]["height"], frame_rate, quality
        )
        print(f"Video export initiated. File will be saved to: {video_path}")

        max_wait_time = 300
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

            time.sleep(1)

    except Exception as e:
        print(f"An error occurred during video export: {str(e)}")
        raise


def main(json_file_path):
    video_info = read_video_info(json_file_path)

    powerpoint = None
    try:
        powerpoint, presentation, slide, elements = create_presentation(video_info)
        add_animations(slide, elements)

        pptx_path = os.path.abspath("intro_test_refined.pptx")
        presentation.SaveAs(pptx_path)
        print(f"Presentation saved to: {pptx_path}")

        video_path = os.path.abspath("intro_test_video_refined.mp4")
        export_to_video(presentation, video_path, video_info)

    except Exception as e:
        print(f"An error occurred: {str(e)}")

    finally:
        if powerpoint:
            powerpoint.Quit()
            pythoncom.CoUninitialize()

    print("Script completed.")


if __name__ == "__main__":
    json_file_path = "video_info.json"
    main(json_file_path)
