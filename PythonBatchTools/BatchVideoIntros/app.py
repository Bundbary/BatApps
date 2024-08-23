import win32com.client
import json
import os
import time
import sys
import gc
import psutil
import traceback
import math


def pixels_to_points(pixels):
    return pixels * 72 / 96  # Convert pixels to points


def force_terminate_powerpoint():
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == "POWERPNT.EXE":
            print(f"Forcefully terminating PowerPoint process (PID: {proc.pid})")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()

def calculate_font_size_from_character_count(char_count):
    if char_count <= 20:
        return 100
    elif char_count <= 30:
        return 87
    elif char_count <= 50:
        return 60
    elif char_count <= 90:
        return 48
    else:
        return 43

def calculate_optimal_font_size(slide, text, max_width, max_height, font_name, min_font_size, max_font_size):
    char_count = len(text)
    font_size = calculate_font_size_from_character_count(char_count)
    print(f"Calculated font size based on {char_count} characters: {font_size}")
    
    # Ensure the font size is within the specified min and max
    final_size = max(min(font_size, max_font_size), min_font_size)
    print(f"Final font size (after min/max adjustment): {final_size}")
    return final_size


def add_textbox_with_dynamic_font(slide, text, left, top, width, height, settings):
    try:
        if settings.get('dynamic_sizing', False):
            font_size = calculate_optimal_font_size(
                slide, text, width, height, 
                settings['font_name'], 
                settings.get('min_font_size', 43), 
                settings.get('max_font_size', 100)
            )
        else:
            font_size = settings['font_size']

        print(f"Adding textbox with font size: {font_size}")

        textbox = slide.Shapes.AddTextbox(1, left, top, width, height)
        textframe = textbox.TextFrame
        textframe.AutoSize = 0  # Disable auto-sizing
        textframe.WordWrap = True

        textrange = textframe.TextRange
        textrange.Text = text
        textrange.ParagraphFormat.Alignment = 1  # Center align
        textrange.ParagraphFormat.SpaceWithin = settings.get('space_within', 1.0)

        font = textrange.Font
        font.Name = settings['font_name']
        font.Size = font_size
        font.Color.RGB = settings['color']

        # Adjust vertical alignment
        text_height = textframe.TextRange.BoundHeight
        if text_height < height:
            textframe.MarginTop = max(0, (height - text_height) / 2)
        else:
            textframe.MarginTop = 0

        print(f"Final textbox height: {textframe.TextRange.BoundHeight}")

        return textbox
    except Exception as e:
        print(f"Error in add_textbox_with_dynamic_font: {str(e)}")
        print(traceback.format_exc())
        return None
      

def create_presentation(video_info_path, layout_settings_path, output_path):
    try:
        with open(video_info_path, "r") as file:
            video_info = json.load(file)

        with open(layout_settings_path, "r") as file:
            layout_settings = json.load(file)

        powerpoint = None
        presentation = None

        try:
            start_time = time.time()
            powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            powerpoint.Visible = True  # Keep PowerPoint visible
            print(f"PowerPoint started in {time.time() - start_time:.2f} seconds")

            start_time = time.time()
            presentation = powerpoint.Presentations.Add()

            # Set slide size
            slide_width = pixels_to_points(video_info["video"]["width"])
            slide_height = pixels_to_points(video_info["video"]["height"])
            presentation.PageSetup.SlideWidth = slide_width
            presentation.PageSetup.SlideHeight = slide_height

            slide = presentation.Slides.Add(1, 12)  # 12 is ppLayoutBlank
            print(
                f"Presentation and slide created in {time.time() - start_time:.2f} seconds"
            )

            # Constants for animations
            ppEffectFade = 1793  # Correct enum value for Fade effect

            shapes = []

            # Layout settings
            margin = pixels_to_points(layout_settings["slide"]["margin"])
            img_width = (
                slide_width * video_info["layout"]["image_width_percentage"] / 100
            )
            content_width = slide_width - img_width - margin * 2

            # Add image placeholder
            img_placeholder = slide.Shapes.AddShape(
                1,  # msoShapeRectangle
                slide_width - img_width,
                0,
                img_width,
                slide_height,
            )
            img_placeholder.Fill.ForeColor.RGB = 13421772  # Light gray
            img_placeholder.Line.Visible = False  # Remove border
            img_placeholder.Name = "ImagePlaceholder"
            shapes.append(img_placeholder)

            current_top = margin

            # Add VIDEO COLLECTION TITLE
            collection_title_height = pixels_to_points(40)
            collection_title = add_textbox_with_dynamic_font(
                slide,
                "VIDEO COLLECTION TITLE",
                margin,
                current_top,
                content_width,
                collection_title_height,
                layout_settings["collection_title"],
            )
            if collection_title is not None:
                collection_title.Name = "CollectionTitle"
                shapes.append(collection_title)
                current_top += collection_title_height + pixels_to_points(20)
            else:
                print("Error: Failed to create collection title")

            
            
            # Add title with dynamic sizing
            title_height = pixels_to_points(240)  # Increased height for title
            title_settings = layout_settings['title'].copy()
            title_settings['dynamic_sizing'] = True
            title_settings['min_font_size'] = 43
            title_settings['max_font_size'] = 100

            title_box = add_textbox_with_dynamic_font(
                slide, video_info['intro']['title'],
                margin, current_top, content_width, title_height,
                title_settings
            )
            if title_box is not None:
                title_box.Name = "TitleBox"
                shapes.append(title_box)
                current_top += title_height + pixels_to_points(20)
            else:
                print("Error: Failed to create title box")
                
            # Add subtitle
            subtitle_height = pixels_to_points(80)  # Increased height for subtitle
            subtitle_box = add_textbox_with_dynamic_font(
                slide,
                video_info["intro"]["subtitle"],
                margin,
                current_top,
                content_width,
                subtitle_height,
                layout_settings["subtitle"],
            )
            if subtitle_box is not None:
                subtitle_box.Name = "SubtitleBox"
                shapes.append(subtitle_box)
                current_top += subtitle_box.Height + pixels_to_points(
                    40
                )  # Increased spacing after subtitle
            else:
                print("Error: Failed to create subtitle box")

            # Add timestamps
            timestamp_height = pixels_to_points(30)
            for i, timestamp in enumerate(video_info["intro"]["timestamps"]):
                ts_box = add_textbox_with_dynamic_font(
                    slide,
                    timestamp,
                    margin,
                    current_top,
                    content_width,
                    timestamp_height,
                    layout_settings["timestamps"],
                )
                if ts_box is not None:
                    ts_box.Name = f"Timestamp{i+1}"
                    shapes.append(ts_box)
                    current_top += timestamp_height + pixels_to_points(
                        layout_settings["timestamps"].get("spacing", 10)
                    )
                else:
                    print(f"Error: Failed to create timestamp box {i+1}")

            # Apply animations
            for shape in shapes:
                try:
                    shape.AnimationSettings.EntryEffect = ppEffectFade
                    shape.AnimationSettings.TextLevelEffect = 1  # Animate as one object
                    shape.AnimationSettings.Animate = True
                    print(f"Applied animation to {shape.Name}")
                except Exception as e:
                    print(f"Error applying animation to shape: {str(e)}")

            start_time = time.time()
            presentation.SaveAs(os.path.abspath(output_path))
            print(f"Presentation saved in {time.time() - start_time:.2f} seconds")

        except Exception as e:
            print(f"An error occurred during presentation creation: {str(e)}")
            print(traceback.format_exc())
        finally:
            if presentation:
                try:
                    presentation.Close()
                except Exception as close_error:
                    print(f"Error closing presentation: {str(close_error)}")
            if powerpoint:
                try:
                    powerpoint.Quit()
                except Exception as quit_error:
                    print(f"Error quitting PowerPoint: {str(quit_error)}")
            print("PowerPoint closed")

            # Force COM objects to be released
            del presentation
            del powerpoint
            gc.collect()

            # Check if PowerPoint is still running and force terminate if necessary
            force_terminate_powerpoint()

    except Exception as outer_error:
        print(f"An outer error occurred: {str(outer_error)}")
        print(traceback.format_exc())


if __name__ == "__main__":
    video_info_path = "video_info.json"
    layout_settings_path = "layout_settings.json"
    output_path = "intro_test.pptx"
    create_presentation(video_info_path, layout_settings_path, output_path)
    print("Script completed.")
