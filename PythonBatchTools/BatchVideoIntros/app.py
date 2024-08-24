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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def pixels_to_points(pixels):
    return pixels * 72 / 96  # Convert pixels to points

def force_terminate_powerpoint():
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == "POWERPNT.EXE":
            logger.info(f"Forcefully terminating PowerPoint process (PID: {proc.pid})")
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()

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
        (float('inf'), 43)  # For any value above 90
    ]
    
    # Find the appropriate range for the character count
    for i, (max_chars, font_size) in enumerate(breakpoints):
        if char_count <= max_chars:
            if i == 0:  # If it's the first breakpoint, return the font size directly
                return font_size
            
            # Interpolate between this breakpoint and the previous one
            prev_max_chars, prev_font_size = breakpoints[i-1]
            char_range = max_chars - prev_max_chars
            font_range = prev_font_size - font_size
            
            # Calculate the interpolated font size
            interpolated_size = prev_font_size - (char_count - prev_max_chars) * (font_range / char_range)
            return round(interpolated_size)
    
    # This line should never be reached due to the float('inf') in the breakpoints,
    # but we'll include it as a fallback
    return 43

def calculate_optimal_font_size(slide, text, max_width, max_height, font_name, min_font_size, max_font_size):
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

        logger.info(f"Adding textbox with font size: {font_size}")

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

        default_settings = animation_settings.get('default', {})
        default_effect = default_settings.get('effect', 10)  # Fade-in effect
        default_delay = default_settings.get('delay', 0.5)
        default_duration = default_settings.get('duration', 0.5)

        total_animation_time = 0

        for i, shape in enumerate(shapes):
            # Determine which animation settings to use
            if shape.Name.startswith('Timestamp'):
                specific_settings = animation_settings.get('timestamps', default_settings)
            else:
                specific_settings = default_settings

            effect_type = specific_settings.get('effect', default_effect)
            delay = specific_settings.get('delay', default_delay)
            duration = specific_settings.get('duration', default_duration)

            # Add effect to the shape
            effect = sequence.AddEffect(shape, effect_type, trigger=ppEffectAfterPrevious)
            effect.Timing.Duration = duration
            
            # Set delay between animations
            if i > 0:
                effect.Timing.TriggerDelayTime = delay

            total_animation_time += delay + duration

        # Set slide transition to advance automatically
        slide.SlideShowTransition.AdvanceOnTime = True
        slide.SlideShowTransition.AdvanceTime = total_animation_time + 1  # Add 1 second after all animations
        slide.SlideShowTransition.Duration = 1  # Duration of the transition effect

        logger.info(f"Applied automatic animations to {len(shapes)} shapes")
        logger.info(f"Set slide to advance automatically after {total_animation_time + 1} seconds")

    except Exception as e:
        logger.error(f"Error applying animations: {str(e)}")
        logger.error(traceback.format_exc())

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
                logger.error("Error: Failed to create collection title")
            
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
                logger.error("Error: Failed to create title box")
                
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
                logger.error("Error: Failed to create subtitle box")

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
                    logger.error(f"Error: Failed to create timestamp box {i+1}")

            # Apply animations
            apply_animations(slide, shapes, layout_settings.get('animations', {}))

            start_time = time.time()
            presentation.SaveAs(os.path.abspath(output_path))
            logger.info(f"Presentation saved in {time.time() - start_time:.2f} seconds")

        except Exception as e:
            logger.error(f"An error occurred during presentation creation: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            if presentation:
                try:
                    presentation.Close()
                except Exception as close_error:
                    logger.error(f"Error closing presentation: {str(close_error)}")
            if powerpoint:
                try:
                    powerpoint.Quit()
                except Exception as quit_error:
                    logger.error(f"Error quitting PowerPoint: {str(quit_error)}")
            logger.info("PowerPoint closed")

            # Force COM objects to be released
            del presentation
            del powerpoint
            gc.collect()

            # Check if PowerPoint is still running and force terminate if necessary
            force_terminate_powerpoint()

    except Exception as outer_error:
        logger.error(f"An outer error occurred: {str(outer_error)}")
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    video_info_path = "video_info.json"
    layout_settings_path = "layout_settings.json"
    output_path = "intro_test.pptx"
    create_presentation(video_info_path, layout_settings_path, output_path)
    logger.info("Script completed.")