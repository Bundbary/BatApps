import win32com.client
import json
import os
import time
import sys
import gc
import psutil
import traceback


def pixels_to_points(pixels):
    return pixels * 72 / 96  # Convert pixels to points


def time_operation(operation_name):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            print(f"{operation_name} took {end_time - start_time:.2f} seconds")
            return result
        return wrapper
    return decorator


def force_terminate_powerpoint():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'POWERPNT.EXE':
            print(f"Forcefully terminating PowerPoint process (PID: {proc.pid})")
            proc.terminate()
            proc.wait(timeout=5)


def add_textbox(slide, text, left, top, width, settings):
    try:
        height = pixels_to_points(settings.get('height', settings['font_size'] * 1.5))
        
        textbox = slide.Shapes.AddTextbox(1, left, top, width, height)
        textframe = textbox.TextFrame
        textframe.TextRange.Text = text
        textframe.TextRange.ParagraphFormat.Alignment = 1  # ppAlignLeft
        textframe.VerticalAnchor = 1  # ppAnchorTop
        textframe.WordWrap = True

        font = textframe.TextRange.Font
        font.Name = settings['font_name']
        font.Size = settings['font_size']
        font.Color.RGB = settings['color']
        
        # Set line spacing
        paragraph_format = textframe.TextRange.ParagraphFormat
        if 'space_within' in settings:
            paragraph_format.SpaceWithin = settings['space_within']

        return textbox
    except Exception as e:
        print(f"Error in add_textbox: {str(e)}")
        print(traceback.format_exc())
        return None
    
       
@time_operation("Total execution")
def create_presentation(video_info_path, layout_settings_path, output_path):
    try:
        with open(video_info_path, 'r') as file:
            video_info = json.load(file)
        
        with open(layout_settings_path, 'r') as file:
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
            slide_width = pixels_to_points(video_info['video']['width'])
            slide_height = pixels_to_points(video_info['video']['height'])
            presentation.PageSetup.SlideWidth = slide_width
            presentation.PageSetup.SlideHeight = slide_height
            
            slide = presentation.Slides.Add(1, 12)  # 12 is ppLayoutBlank
            print(f"Presentation and slide created in {time.time() - start_time:.2f} seconds")

            # Constants for animations
            ppEffectFade = 1793  # Correct enum value for Fade effect

            shapes = []

            # Layout settings
            margin = pixels_to_points(layout_settings['slide']['margin'])
            img_width = slide_width * video_info['layout']['image_width_percentage'] / 100
            content_width = slide_width - img_width - margin * 2

            # Add image placeholder
            img_placeholder = slide.Shapes.AddShape(
                1,  # msoShapeRectangle
                slide_width - img_width,
                0,
                img_width,
                slide_height
            )
            img_placeholder.Fill.ForeColor.RGB = 13421772  # Light gray
            img_placeholder.Line.Visible = False  # Remove border
            img_placeholder.Name = "ImagePlaceholder"
            shapes.append(img_placeholder)

            current_top = margin

            # Add VIDEO COLLECTION TITLE
            collection_title = add_textbox(
                slide, "VIDEO COLLECTION TITLE", 
                margin, current_top, content_width,
                layout_settings['collection_title']
            )
            collection_title.Name = "CollectionTitle"
            shapes.append(collection_title)
            current_top += collection_title.Height + pixels_to_points(20)

            # Add title
            title_box = add_textbox(
                slide, video_info['intro']['title'],
                margin, current_top, content_width,
                layout_settings['title']
            )
            title_box.Name = "TitleBox"
            shapes.append(title_box)
            current_top += title_box.Height + pixels_to_points(20)

            # Add subtitle
            subtitle_box = add_textbox(
                slide, video_info['intro']['subtitle'],
                margin, current_top, content_width,
                layout_settings['subtitle']
            )
            subtitle_box.Name = "SubtitleBox"
            shapes.append(subtitle_box)
            current_top += subtitle_box.Height + pixels_to_points(30)

            # Add timestamps
            for i, timestamp in enumerate(video_info['intro']['timestamps']):
                ts_box = add_textbox(
                    slide, timestamp,
                    margin, current_top, content_width,
                    layout_settings['timestamps']
                )
                ts_box.Name = f"Timestamp{i+1}"
                shapes.append(ts_box)
                current_top += ts_box.Height + pixels_to_points(layout_settings['timestamps'].get('spacing', 10))

            # Apply animations
            for shape in shapes:
                try:
                    if shape is not None:
                        shape.AnimationSettings.EntryEffect = ppEffectFade
                        shape.AnimationSettings.TextLevelEffect = 1  # Animate as one object
                        shape.AnimationSettings.Animate = True
                        print(f"Applied animation to {shape.Name}")
                    else:
                        print(f"Skipping animation for null shape")
                except Exception as e:
                    print(f"Error applying animation to {shape.Name}: {str(e)}")

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