import win32com.client
import json
import os
import time
import sys
import gc
import psutil
import traceback
import math
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def pixels_to_points(pixels):
    return pixels * 72 / 96  # Convert pixels to points


# def force_terminate_powerpoint():
#     for proc in psutil.process_iter(["name"]):
#         if proc.info["name"] == "POWERPNT.EXE":
#             logger.info(f"Forcefully terminating PowerPoint process (PID: {proc.pid})")
#             try:
#                 proc.terminate()
#                 proc.wait(timeout=5)
#             except psutil.TimeoutExpired:
#                 proc.kill()

def force_terminate_powerpoint():
    for proc in psutil.process_iter(['name']):
        if proc.info['name'] == 'POWERPNT.EXE':
            logger.info(f"Forcefully terminating PowerPoint process (PID: {proc.pid})")
            try:
                proc.kill()  # Use kill instead of terminate for immediate termination
            except psutil.NoSuchProcess:
                pass  # Process already terminated
            except Exception as e:
                logger.error(f"Error terminating PowerPoint process: {str(e)}")
def calculate_font_size_from_character_count(char_count):
    logger.info(f"Character count: {char_count}")

    # Define the breakpoints and corresponding font sizes
    breakpoints = [
        (25, 100),
        (30, 90),
        (40, 69),
        (50, 60),
        (70, 56),
        (80, 50),
        (90, 48),
        (float("inf"), 43),  # For any value above 90
    ]

    # Find the appropriate range for the character count
    for i, (max_chars, font_size) in enumerate(breakpoints):
        if char_count <= max_chars:
            if i == 0:  # If it's the first breakpoint, return the font size directly
                return font_size

            # Interpolate between this breakpoint and the previous one
            prev_max_chars, prev_font_size = breakpoints[i - 1]
            char_range = max_chars - prev_max_chars
            font_range = prev_font_size - font_size

            # Calculate the interpolated font size
            interpolated_size = prev_font_size - (char_count - prev_max_chars) * (
                font_range / char_range
            )
            return round(interpolated_size)

    # This line should never be reached due to the float('inf') in the breakpoints,
    # but we'll include it as a fallback
    return 43


def calculate_optimal_font_size(
    slide, text, max_width, max_height, font_name, min_font_size, max_font_size
):
    shape = slide.Shapes.AddTextbox(1, 0, 0, max_width, max_height)
    text_frame = shape.TextFrame
    text_frame.WordWrap = True
    text_frame.AutoSize = 0  # Disable auto-sizing
    text_range = text_frame.TextRange
    text_range.Text = text
    text_range.ParagraphFormat.Alignment = 1  # Center align

    def measure_text(font_size):
        text_range.Font.Size = font_size
        text_range.Font.Name = font_name
        return text_frame.TextRange.BoundHeight, text_frame.TextRange.BoundWidth

    # Binary search to find the optimal font size
    low, high = min_font_size, max_font_size
    optimal_size = min_font_size
    while low <= high:
        mid = (low + high) // 2
        height, width = measure_text(mid)
        if height <= max_height and width <= max_width:
            optimal_size = mid
            low = mid + 1
        else:
            high = mid - 1

    # Fine-tune: decrease font size until it fits
    while optimal_size > min_font_size:
        height, width = measure_text(optimal_size)
        if height <= max_height and width <= max_width:
            break
        optimal_size -= 1

    shape.Delete()
    logger.info(f"Optimal font size: {optimal_size}")
    return optimal_size


def format_timestamp(text, time, max_width, font_name, font_size, slide):
    # Helper function to measure text width
    def measure_text_width(text, font_name, font_size):
        temp_shape = slide.Shapes.AddTextbox(1, 0, 0, 100, 20)
        temp_shape.TextFrame.TextRange.Text = text
        temp_shape.TextFrame.TextRange.Font.Name = font_name
        temp_shape.TextFrame.TextRange.Font.Size = font_size
        width = temp_shape.TextFrame.TextRange.BoundWidth
        temp_shape.Delete()
        return width

    # Measure the width of the text and time
    text_width = measure_text_width(text, font_name, font_size)
    time_width = measure_text_width(time, font_name, font_size)

    # Calculate available space for dots
    available_space = max_width - text_width - time_width

    # Calculate the number of dots that can fit
    dot_width = measure_text_width(".", font_name, font_size)
    num_dots = max(0, int(available_space / dot_width))

    # Construct the formatted timestamp
    formatted_timestamp = f"{text} {' ' * num_dots} {time}"

    return formatted_timestamp

def add_textbox_with_dynamic_font(slide, text, left, top, width, height, settings, disable_word_wrap=False, justify=False):
    try:
        if settings.get("dynamic_sizing", False):
            font_size = calculate_optimal_font_size(
                slide,
                text,
                width,
                height,
                settings["font_name"],
                settings.get("min_font_size", 43),
                settings.get("max_font_size", 100),
            )
        else:
            font_size = settings["font_size"]

        logger.info(f"Adding textbox with font size: {font_size}")

        textbox = slide.Shapes.AddTextbox(1, left, top, width, height)
        textframe = textbox.TextFrame
        textframe.AutoSize = 0  # Disable auto-sizing
        textframe.WordWrap = not disable_word_wrap  # Set word wrap based on parameter


        textrange = textframe.TextRange
        textrange.Text = text
        textrange.ParagraphFormat.Alignment = 3 if justify else 1  # 3 for justified, 1 for center align
        textrange.ParagraphFormat.SpaceWithin = settings.get("space_within", 1.0)


        font = textrange.Font
        font.Name = settings["font_name"]
        font.Size = font_size
        font.Color.RGB = settings["color"]

        # Adjust vertical alignment
        text_height = textframe.TextRange.BoundHeight
        if text_height < height:
            textframe.MarginTop = max(0, (height - text_height) / 2)
        else:
            textframe.MarginTop = 0

        logger.info(f"Final textbox height: {textframe.TextRange.BoundHeight}")

        return textbox
    except Exception as e:
        logger.error(f"Error in add_textbox_with_dynamic_font: {str(e)}")
        logger.error(traceback.format_exc())
        return None
    
def apply_animations(slide, shapes, animation_settings):
    try:
        sequence = slide.TimeLine.MainSequence

        # Constants for animation triggers
        ppEffectOnClick = 1
        ppEffectWithPrevious = 2
        ppEffectAfterPrevious = 3

        default_settings = animation_settings.get("default", {})
        default_effect = default_settings.get("effect", 10)  # Fade-in effect
        default_delay = default_settings.get("delay", 0.5)
        default_duration = default_settings.get("duration", 0.5)
        text_display_duration = animation_settings.get(
            "text_display_duration", 5
        )  # New setting

        total_animation_time = 0

        for i, shape in enumerate(shapes):
            # Determine which animation settings to use
            if shape.Name.startswith("Timestamp"):
                specific_settings = animation_settings.get(
                    "timestamps", default_settings
                )
            else:
                specific_settings = default_settings

            effect_type = specific_settings.get("effect", default_effect)
            delay = specific_settings.get("delay", default_delay)
            duration = specific_settings.get("duration", default_duration)

            # Add effect to the shape
            effect = sequence.AddEffect(
                shape, effect_type, trigger=ppEffectAfterPrevious
            )
            effect.Timing.Duration = duration

            # Set delay between animations
            if i > 0:
                effect.Timing.TriggerDelayTime = delay

            total_animation_time += delay + duration

        # Calculate total slide duration
        total_slide_duration = total_animation_time + text_display_duration

        # Set slide transition to advance automatically
        slide.SlideShowTransition.AdvanceOnTime = True
        slide.SlideShowTransition.AdvanceTime = total_slide_duration
        slide.SlideShowTransition.Duration = 1  # Duration of the transition effect

        logger.info(f"Applied automatic animations to {len(shapes)} shapes")
        logger.info(f"Total animation time: {total_animation_time:.2f} seconds")
        logger.info(f"Text display duration: {text_display_duration:.2f} seconds")
        logger.info(
            f"Set slide to advance automatically after {total_slide_duration:.2f} seconds"
        )

    except Exception as e:
        logger.error(f"Error applying animations: {str(e)}")
        logger.error(traceback.format_exc())


def build_timestamp_with_dots(slide, text, time_str, max_width, font_name, font_size):
    def measure_text_width(text):
        temp_shape = slide.Shapes.AddTextbox(1, 0, 0, max_width, 20)
        temp_shape.TextFrame.TextRange.Text = text
        temp_shape.TextFrame.TextRange.Font.Name = font_name
        temp_shape.TextFrame.TextRange.Font.Size = font_size
        temp_shape.TextFrame.WordWrap = False  # Ensure no word wrap
        width = temp_shape.TextFrame.TextRange.BoundWidth
        temp_shape.Delete()
        return width

    text_width = measure_text_width(text)
    time_width = measure_text_width(time_str)
    dot_width = measure_text_width(".")

    available_width = max_width - text_width - time_width - dot_width  # Space for one dot (minimum)
    num_dots = max(1, int(available_width / dot_width))

    formatted_text = f"{text} {'.' * num_dots} {time_str}"
    
    while measure_text_width(formatted_text) < max_width:
        num_dots += 1
        formatted_text = f"{text} {'.' * num_dots} {time_str}"
    
    while measure_text_width(formatted_text) > max_width and num_dots > 1:
        num_dots -= 1
        formatted_text = f"{text} {'.' * num_dots} {time_str}"

    return formatted_text

def create_presentation(video_info_path, layout_settings_path, output_pptx_path, output_video_path):
    try:
        with open(video_info_path, "r") as file:
            video_info = json.load(file)

        with open(layout_settings_path, "r") as file:
            layout_settings = json.load(file)

        logger.info("Starting presentation creation")

        powerpoint = None
        presentation = None

        try:
            start_time = time.time()
            powerpoint = win32com.client.Dispatch("PowerPoint.Application")
            powerpoint.Visible = True  # Keep PowerPoint visible
            logger.info(f"PowerPoint started in {time.time() - start_time:.2f} seconds")

            start_time = time.time()
            presentation = powerpoint.Presentations.Add()

            # Set slide size
            slide_width = pixels_to_points(video_info["video"]["width"])
            slide_height = pixels_to_points(video_info["video"]["height"])
            presentation.PageSetup.SlideWidth = slide_width
            presentation.PageSetup.SlideHeight = slide_height

            slide = presentation.Slides.Add(1, 12)  # 12 is ppLayoutBlank
            logger.info(f"Presentation and slide created in {time.time() - start_time:.2f} seconds")

            shapes = []

            # Layout settings
            margin = pixels_to_points(layout_settings["slide"]["margin"])
            img_width = (slide_width * video_info["layout"]["image_width_percentage"] / 100)
            content_width = slide_width - img_width - margin * 2

            logger.info("Adding main content elements")

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
            logger.info("Added image placeholder")

            current_top = margin

            # Add VIDEO COLLECTION TITLE
            logger.info("Adding collection title")
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
                logger.info("Collection title added successfully")
            else:
                logger.error("Error: Failed to create collection title")

            # Add title with dynamic sizing
            logger.info("Adding main title")
            title_height = pixels_to_points(240)  # Increased height for title
            title_settings = layout_settings['title'].copy()
            title_settings['dynamic_sizing'] = True
            title_settings['min_font_size'] = 43
            title_settings['max_font_size'] = 100

            title_box = add_textbox_with_dynamic_font(
                slide,
                video_info['intro']['title'],
                margin,
                current_top,
                content_width,
                title_height,
                title_settings,
            )
            if title_box is not None:
                title_box.Name = "TitleBox"
                shapes.append(title_box)
                current_top += title_height + pixels_to_points(20)
                logger.info("Main title added successfully")
            else:
                logger.error("Error: Failed to create title box")

            # Add subtitle
            logger.info("Adding subtitle")
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
                current_top += subtitle_box.Height + pixels_to_points(40)  # Increased spacing after subtitle
                logger.info("Subtitle added successfully")
            else:
                logger.error("Error: Failed to create subtitle box")

            # Add timestamps
            logger.info(f"Starting to add {len(video_info['intro']['timestamps'])} timestamps")
            timestamp_height = pixels_to_points(30)

            for i, timestamp in enumerate(video_info["intro"]["timestamps"]):
                logger.info(f"Processing timestamp {i+1}: {timestamp['text']}")
                formatted_text = build_timestamp_with_dots(
                    slide,
                    timestamp["text"],
                    timestamp["time"],
                    content_width,
                    layout_settings["timestamps"]["font_name"],
                    layout_settings["timestamps"]["font_size"]
                )
                logger.info(f"Formatted timestamp {i+1}: {formatted_text}")
                ts_box = add_textbox_with_dynamic_font(
                    slide,
                    formatted_text,
                    margin,
                    current_top,
                    content_width,
                    timestamp_height,
                    layout_settings["timestamps"],
                    disable_word_wrap=True,
                    justify=True
                )
                if ts_box is not None:
                    ts_box.Name = f"Timestamp{i+1}"
                    shapes.append(ts_box)
                    current_top += timestamp_height + pixels_to_points(
                        layout_settings["timestamps"].get("spacing", 10)
                    )
                    logger.info(f"Added timestamp {i+1} successfully")
                else:
                    logger.error(f"Error: Failed to create timestamp box {i+1}")

            logger.info("Finished adding timestamps")

            # Apply animations
            logger.info("Applying animations")
            apply_animations(slide, shapes, layout_settings.get("animations", {}))

            logger.info("Saving presentation")
            start_time = time.time()
            presentation.SaveAs(os.path.abspath(output_pptx_path))
            logger.info(f"Presentation saved in {time.time() - start_time:.2f} seconds")
    
            # Export to video
            logger.info("Exporting presentation to video")
            export_to_video(presentation, output_video_path)

            # Force terminate PowerPoint immediately after video export
            logger.info("Force terminating PowerPoint")
            force_terminate_powerpoint()

        except Exception as e:
            logger.error(f"An error occurred during presentation creation or video export: {str(e)}")
            logger.error(traceback.format_exc())
            # Force terminate PowerPoint in case of an exception
            logger.info("Force terminating PowerPoint due to exception")
            force_terminate_powerpoint()
        finally:
            # These operations might not be necessary now, but we'll keep them as a safeguard
            if presentation:
                try:
                    presentation.Close()
                except Exception:
                    pass
            if powerpoint:
                try:
                    powerpoint.Quit()
                except Exception:
                    pass
            logger.info("PowerPoint handling completed")

            # Force COM objects to be released
            del presentation
            del powerpoint
            gc.collect()

    except Exception as outer_error:
        logger.error(f"An outer error occurred: {str(outer_error)}")
        logger.error(traceback.format_exc())

    logger.info("Presentation creation and video export process completed")



import os

def export_to_video(presentation, output_path):
    try:
        # Ensure the output path is absolute
        abs_output_path = os.path.abspath(output_path)
        
        # Get the directory of the output path
        output_dir = os.path.dirname(abs_output_path)
        
        # Ensure the directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if the file already exists and delete it if it does
        if os.path.exists(abs_output_path):
            logger.info(f"Existing video file found. Deleting: {abs_output_path}")
            os.remove(abs_output_path)
        
        # Set video export settings
        presentation.CreateVideo(abs_output_path)
        
        logger.info(f"Starting video export to {abs_output_path}...")
        
        # Check for file existence and size every second
        start_time = time.time()
        while True:
            if os.path.exists(abs_output_path) and os.path.getsize(abs_output_path) > 0:
                logger.info(f"Video export completed successfully: {abs_output_path}")
                return True
            
            if time.time() - start_time > 300:  # 5 minutes timeout
                logger.error("Video export timed out after 5 minutes")
                return False
            
            time.sleep(1)  # Wait for 1 second before checking again
        
    except Exception as e:
        logger.error(f"Error during video export: {str(e)}")
        logger.error(traceback.format_exc())
        return False
    

if __name__ == "__main__":
    video_info_path = "video_info.json"
    layout_settings_path = "layout_settings.json"
    output_pptx_path = "intro_test.pptx"
    output_video_path = "intro_test.mp4"  # This will be in the same folder as the script
    create_presentation(video_info_path, layout_settings_path, output_pptx_path, output_video_path)
    logger.info("Script completed.")