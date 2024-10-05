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
import subprocess
import shutil
import requests
import time

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def generate_timestamped_filename(base_name, extension):
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    print(f"foo: {base_name}_{timestamp}.{extension}")
    return f"{base_name}_{timestamp}.{extension}"


def pixels_to_points(pixels):
    return pixels * 72 / 96  # Convert pixels to points


def convert_video(input_file, output_dir):
    logger.info(f"Starting video conversion for: {input_file}")

    file_name = os.path.basename(input_file)

    # Get video duration
    duration_command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        input_file,
    ]
    duration_result = subprocess.run(duration_command, capture_output=True, text=True)
    duration = float(duration_result.stdout.strip())

    # Calculate fade start time (1 second before the end)
    fade_start = max(0, duration - 1)

    # Prepare output file path
    output_file = os.path.join(output_dir, f"converted_{file_name}")

    # Convert video with fade-out
    ffmpeg_command = [
        "ffmpeg",
        "-i",
        input_file,
        "-c:v",
        "libx264",
        "-profile:v",
        "high",
        "-preset",
        "medium",
        "-crf",
        "23",
        "-vf",
        f"fps=30,format=yuv420p,fade=t=out:st={fade_start}:d=1",  # Add fade-out filter
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        output_file,
        "-y",
    ]

    try:
        subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        logger.info(f"Successfully converted {file_name} with fade-out")

        # Verify the converted file
        ffprobe_command = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-count_packets",
            "-show_entries",
            "stream=r_frame_rate,avg_frame_rate",
            "-of",
            "csv=p=0",
            output_file,
        ]
        result = subprocess.run(ffprobe_command, capture_output=True, text=True)
        logger.info(f"Converted file details:\n{result.stdout}")

        # If everything is successful, replace the original file with the converted one
        os.replace(output_file, input_file)
        logger.info(f"Replaced original file with converted file: {input_file}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting {file_name}: {e}")
        logger.error(f"FFmpeg error output: {e.stderr}")
        # Clean up the output file if it was created
        if os.path.exists(output_file):
            os.remove(output_file)
        raise

    logger.info(f"Video conversion completed for: {input_file}")


def force_terminate_powerpoint():
    for proc in psutil.process_iter(["name"]):
        if proc.info["name"] == "POWERPNT.EXE":
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


def add_textbox_with_dynamic_font(
    slide,
    text,
    left,
    top,
    width,
    height,
    settings,
    disable_word_wrap=False,
    justify=False,
):
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
        textrange.ParagraphFormat.Alignment = (
            3 if justify else 1
        )  # 3 for justified, 1 for center align
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
            elif shape.Name.startswith("BulletPoint"):
                specific_settings = animation_settings.get("bullets", default_settings)
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

    available_width = (
        max_width - text_width - time_width - dot_width
    )  # Space for one dot (minimum)
    num_dots = max(1, int(available_width / dot_width))

    formatted_text = f"{text} {'.' * num_dots} {time_str}"

    while measure_text_width(formatted_text) < max_width:
        num_dots += 1
        formatted_text = f"{text} {'.' * num_dots} {time_str}"

    while measure_text_width(formatted_text) > max_width and num_dots > 1:
        num_dots -= 1
        formatted_text = f"{text} {'.' * num_dots} {time_str}"

    return formatted_text


def setup_project_directory(output_dir, base_folder_url):
    project_name = os.path.basename(base_folder_url.rstrip("/"))
    remote_projects_dir = os.path.join(output_dir, "remote_projects")
    project_dir = os.path.join(remote_projects_dir, project_name)
    os.makedirs(project_dir, exist_ok=True)
    return project_name, project_dir


def initialize_powerpoint(layout_settings):
    powerpoint = win32com.client.Dispatch("PowerPoint.Application")
    powerpoint.Visible = True
    presentation = powerpoint.Presentations.Add()
    slide_width = pixels_to_points(layout_settings["video"]["width"])
    slide_height = pixels_to_points(layout_settings["video"]["height"])
    presentation.PageSetup.SlideWidth = slide_width
    presentation.PageSetup.SlideHeight = slide_height
    return powerpoint, presentation, slide_width, slide_height


def create_slide(presentation):
    return presentation.Slides.Add(1, 12)  # 12 is ppLayoutBlank


def add_background_image(
    slide, image_url, image_filename, project_dir, slide_width, slide_height
):
    image_path = download_file(image_url, image_filename, project_dir)
    if image_path:
        try:
            background_image = slide.Shapes.AddPicture(
                FileName=image_path,
                LinkToFile=False,
                SaveWithDocument=True,
                Left=0,
                Top=0,
                Width=slide_width,
                Height=slide_height,
            )
            background_image.ZOrder(3)  # Send to back
            logger.info(
                f"Added full-size intro image as shape successfully: {image_path}"
            )
        except Exception as e:
            logger.error(f"Error adding full-size intro image as shape: {str(e)}")
    else:
        logger.warning(f"Failed to download intro image from: {image_url}")


def add_text_overlay(slide, text_area_width, slide_height):
    text_area = slide.Shapes.AddShape(1, 0, 0, text_area_width, slide_height)
    text_area.Fill.ForeColor.RGB = 0xFFFFFF  # White color
    text_area.Line.Visible = False
    text_area.Name = "TextArea"
    return text_area


def add_collection_title(slide, video_info, margin, content_width, layout_settings):
    collection_title_height = pixels_to_points(40)
    collection_title = add_textbox_with_dynamic_font(
        slide,
        video_info["collection_title"],
        margin,
        margin,
        content_width,
        collection_title_height,
        layout_settings["collection_title"],
    )
    if collection_title is not None:
        collection_title.Name = "CollectionTitle"
        return collection_title, collection_title_height + pixels_to_points(20)
    else:
        logger.error("Error: Failed to create collection title")
        return None, 0


def add_main_title(
    slide, video_info, margin, current_top, content_width, layout_settings
):
    title_height = pixels_to_points(240)
    title_settings = layout_settings["title"].copy()
    title_settings["dynamic_sizing"] = True
    title_settings["min_font_size"] = 43
    title_settings["max_font_size"] = 100
    title_box = add_textbox_with_dynamic_font(
        slide,
        video_info["title"],
        margin,
        current_top,
        content_width,
        title_height,
        title_settings,
    )
    if title_box is not None:
        title_box.Name = "TitleBox"
        return title_box, title_height + pixels_to_points(20)
    else:
        logger.error("Error: Failed to create title box")
        return None, 0


def add_subtitle(
    slide, video_info, margin, current_top, content_width, layout_settings
):
    subtitle_height = pixels_to_points(80)
    subtitle_box = add_textbox_with_dynamic_font(
        slide,
        video_info["subtitle"],
        margin,
        current_top,
        content_width,
        subtitle_height,
        layout_settings["subtitle"],
    )
    if subtitle_box is not None:
        subtitle_box.Name = "SubtitleBox"
        subtitle_box.TextFrame.AutoSize = 1  # ppAutoSizeShapeToFitText
        actual_text_height = subtitle_box.TextFrame.TextRange.BoundHeight
        subtitle_box.Height = actual_text_height
        return subtitle_box, subtitle_box.Top + actual_text_height
    else:
        logger.error("Error: Failed to create subtitle box")
        return None, current_top + subtitle_height


def add_bullet_points(
    slide, video_info, margin, current_top, content_width, layout_settings
):
    bullet_shapes = []
    if "bullets" in video_info:
        bullet_settings = layout_settings["bullets"]
        bullet_spacing = pixels_to_points(bullet_settings.get("spacing", 10))

        for i, bullet_text in enumerate(video_info["bullets"]):
            bullet_box = add_bullet_point(
                slide,
                bullet_text,
                margin,
                current_top,
                content_width,
                pixels_to_points(30),
                bullet_settings,
            )
            if bullet_box is not None:
                bullet_box.Name = f"BulletPoint{i+1}"
                bullet_box.TextFrame.AutoSize = 1  # ppAutoSizeShapeToFitText
                bullet_shapes.append(bullet_box)
                current_top += bullet_box.Height + bullet_spacing
            else:
                logger.error(f"Error: Failed to create bullet point {i+1}")

        current_top += bullet_spacing  # Extra space after last bullet

    return bullet_shapes, current_top


def add_timestamps(
    slide, video_info, margin, current_top, content_width, layout_settings
):
    timestamp_shapes = []
    timestamp_height = pixels_to_points(30)
    timestamp_spacing = pixels_to_points(
        layout_settings["timestamps"].get("spacing", 10)
    )

    for i, timestamp in enumerate(video_info["timestamps"]):
        formatted_text = build_timestamp_with_dots(
            slide,
            timestamp["text"],
            timestamp["time"],
            content_width,
            layout_settings["timestamps"]["font_name"],
            layout_settings["timestamps"]["font_size"],
        )
        ts_box = add_textbox_with_dynamic_font(
            slide,
            formatted_text,
            margin,
            current_top,
            content_width,
            timestamp_height,
            layout_settings["timestamps"],
            disable_word_wrap=True,
            justify=True,
        )
        if ts_box is not None:
            ts_box.Name = f"Timestamp{i+1}"
            timestamp_shapes.append(ts_box)
            current_top += ts_box.Height + timestamp_spacing
        else:
            logger.error(f"Error: Failed to create timestamp box {i+1}")

    return timestamp_shapes, current_top


def finalize_presentation(
    presentation,
    shapes,
    output_pptx_path,
    output_video_path,
    layout_settings,
    project_dir,
):
    apply_animations(
        presentation.Slides(1), shapes, layout_settings.get("animations", {})
    )

    logger.info("Saving presentation")
    start_time = time.time()
    presentation.SaveAs(os.path.abspath(output_pptx_path))
    logger.info(f"Presentation saved in {time.time() - start_time:.2f} seconds")

    logger.info("Exporting presentation to video")
    export_to_video(presentation, output_video_path, layout_settings)

    logger.info("Force terminating PowerPoint")
    force_terminate_powerpoint()

    logger.info("Starting video conversion")
    convert_video(output_video_path, project_dir)



def create_presentation(video_info, layout_settings_path, output_dir, base_folder_url):
    try:
        project_name, project_dir = setup_project_directory(output_dir, base_folder_url)
        logger.info(f"Starting presentation creation for {project_name}")
        
        # Modify video_info (add timestamps, etc.) before splitting
        video_info = prepend_intro_timestamp(video_info)
        
        # Explicitly create global_props and video_specific_info
        global_props = video_info.copy()
        video_specific_info = {
            'duration': global_props.pop('duration', ''),
            'transcript': global_props.pop('transcript', []),
            'label': 'intro'  # Add the new 'label' field
        }
        
        logger.info(f"Initial global_props keys: {global_props.keys()}")
        logger.info(f"Initial video_specific_info keys: {video_specific_info.keys()}")
        
        with open(layout_settings_path, "r") as file:
            layout_settings = json.load(file)
        
        # Generate a single timestamp
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Create base filename with timestamp
        base_filename = f"{project_name}_{timestamp}"
        
        # Generate filenames for MP4 and JSON
        mp4_filename = f"{base_filename}.mp4"
        json_filename = f"{base_filename}.json"
        
        logger.info(f"Generated base filename: {base_filename}")
        logger.info(f"MP4 filename: {mp4_filename}")
        logger.info(f"JSON filename: {json_filename}")
        
        output_pptx_path = os.path.join(project_dir, f"{project_name}.pptx")
        output_video_path = os.path.join(project_dir, mp4_filename)
        output_json_path = os.path.join(project_dir, json_filename)
        
        # Update the 'order' array in global_props
        if 'order' in global_props:
            global_props['order'] = [mp4_filename if item == 'global_props.mp4' else item for item in global_props['order']]
        else:
            logger.warning("No 'order' array found in global_props")
        
        powerpoint = None
        presentation = None
        try:
            powerpoint, presentation, slide_width, slide_height = initialize_powerpoint(layout_settings)
            slide = create_slide(presentation)
            
            margin = pixels_to_points(layout_settings["slide"]["margin"])
            text_area_width = slide_width * 0.4
            content_width = text_area_width - margin * 2
            
            image_url = f"{base_folder_url}/intro_image.jpg"
            add_background_image(slide, image_url, 'intro_image.jpg', project_dir, slide_width, slide_height)
            
            text_area = add_text_overlay(slide, text_area_width, slide_height)
            shapes = [text_area]
            
            current_top = margin
            
            collection_title, height = add_collection_title(slide, global_props, margin, content_width, layout_settings)
            if collection_title:
                shapes.append(collection_title)
                current_top += height
            
            title_box, height = add_main_title(slide, global_props, margin, current_top, content_width, layout_settings)
            if title_box:
                shapes.append(title_box)
                current_top += height
            
            subtitle_box, subtitle_bottom = add_subtitle(slide, global_props, margin, current_top, content_width, layout_settings)
            if subtitle_box:
                shapes.append(subtitle_box)
                current_top = subtitle_bottom + pixels_to_points(20)
            
            bullet_shapes, current_top = add_bullet_points(slide, global_props, margin, current_top, content_width, layout_settings)
            shapes.extend(bullet_shapes)
            
            timestamp_shapes, _ = add_timestamps(slide, global_props, margin, current_top, content_width, layout_settings)
            shapes.extend(timestamp_shapes)
            
            finalize_presentation(presentation, shapes, output_pptx_path, output_video_path, layout_settings, project_dir)
            
        except Exception as inner_error:
            logger.error(f"An error occurred during presentation creation: {str(inner_error)}")
            logger.error(traceback.format_exc())
            raise
        finally:
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
            
            del presentation
            del powerpoint
            gc.collect()
        
        # Save the global_props.json file
        global_props_path = os.path.join(project_dir, "global_props.json")
        with open(global_props_path, 'w', encoding='utf-8') as json_file:
            json.dump(global_props, json_file, ensure_ascii=False, indent=4)
        logger.info(f"Saved global_props.json to {global_props_path}")
        logger.info(f"Final global_props keys: {global_props.keys()}")
        
        # Save the video-specific JSON file with the timestamped filename
        with open(output_json_path, 'w', encoding='utf-8') as json_file:
            json.dump(video_specific_info, json_file, ensure_ascii=False, indent=4)
        logger.info(f"Saved video-specific JSON to {output_json_path}")
        logger.info(f"Final video_specific_info keys: {video_specific_info.keys()}")
        
        # Verify file contents
        with open(global_props_path, 'r', encoding='utf-8') as f:
            saved_global_props = json.load(f)
            logger.info(f"Verified global_props.json contents. Keys: {saved_global_props.keys()}")
        
        with open(output_json_path, 'r', encoding='utf-8') as f:
            saved_video_specific = json.load(f)
            logger.info(f"Verified {json_filename} contents. Keys: {saved_video_specific.keys()}")
        
        logger.info(f"Returning from create_presentation. project_name: {project_name}, base_filename: {base_filename}")
        return project_name, base_filename
        
    except Exception as outer_error:
        logger.error(f"An outer error occurred during presentation creation: {str(outer_error)}")
        logger.error(traceback.format_exc())
        force_terminate_powerpoint()
    
    logger.info(f"Presentation creation and video export process completed for {project_name}")



def process_folder(input_folder, layout_settings_path):
    logger.info(f"Starting batch processing for folder: {input_folder}")

    if not os.path.exists(input_folder):
        logger.error(f"Input folder does not exist: {input_folder}")
        return

    for root, dirs, files in os.walk(input_folder):
        if "_backups" in dirs:
            dirs.remove("_backups")

        global_props_file = "global_props.json"
        video_info_path = os.path.join(root, global_props_file)

        if os.path.exists(video_info_path):
            output_dir = root
            logger.info(f"Processing file: {video_info_path}")
            try:
                create_presentation(video_info_path, layout_settings_path, output_dir)
            except Exception as e:
                logger.error(f"Failed to process {video_info_path}: {str(e)}")
                logger.error("Continuing with next presentation...")
            logger.info(f"Completed processing for: {video_info_path}")
        else:
            logger.info(f"Skipping folder {root}: global_props.json not found")

    logger.info("Batch processing completed")


def export_to_video(presentation, output_path, layout_settings):
    try:
        # Ensure the output path is absolute
        abs_output_path = os.path.abspath(output_path)
        output_dir = os.path.dirname(abs_output_path)
        os.makedirs(output_dir, exist_ok=True)

        # Check if the file already exists and delete it if it does
        if os.path.exists(abs_output_path):
            logger.info(f"Existing video file found. Deleting: {abs_output_path}")
            os.remove(abs_output_path)

        # Get the video dimensions from layout settings
        video_width = layout_settings["video"]["width"]
        video_height = layout_settings["video"]["height"]

        # Set video export settings with dimensions from layout settings
        presentation.CreateVideo(
            abs_output_path, UseTimingsAndNarrations=True, VertResolution=video_height
        )

        logger.info(
            f"Starting video export to {abs_output_path} at {video_width}x{video_height}..."
        )

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


def add_bullet_point(slide, text, left, top, width, height, settings):
    try:
        shape = slide.Shapes.AddTextbox(1, left, top, width, height)
        text_frame = shape.TextFrame
        text_range = text_frame.TextRange

        # Set the text and enable bullet
        text_range.Text = text
        text_range.ParagraphFormat.Bullet.Visible = True

        # Set bullet character (you can change this if needed)
        text_range.ParagraphFormat.Bullet.Character = 8226  # Unicode for bullet (•)

        # Set bullet size relative to text
        text_range.ParagraphFormat.Bullet.RelativeSize = 1.0

        # Set font properties
        font = text_range.Font
        font.Name = settings["font_name"]
        font.Size = settings["font_size"]
        font.Color.RGB = settings["color"]
        return shape
    except Exception as e:
        logger.error(f"Error in add_bullet_point: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def cleanup_duplicate_entries(video_info):
    # Remove duplicate 'global_props.mp4' from order
    if "order" in video_info:
        video_info["order"] = ["global_props.mp4"] + [
            item for item in video_info["order"] if item != "global_props.mp4"
        ]

    # Remove duplicate Introduction timestamps
    if "timestamps" in video_info:
        seen_intro = False
        cleaned_timestamps = []
        for ts in video_info["timestamps"]:
            if ts["text"] == "Introduction" and ts["time"] == "00:00:00":
                if not seen_intro:
                    cleaned_timestamps.append(ts)
                    seen_intro = True
            else:
                cleaned_timestamps.append(ts)
        video_info["timestamps"] = cleaned_timestamps

    return video_info


def prepend_intro_timestamp(video_info):
    try:
        logger.info(
            f"Processing video info. Keys present: {', '.join(video_info.keys())}"
        )

        # Clean up any existing duplicate entries
        video_info = cleanup_duplicate_entries(video_info)
        # Check for required keys
        required_keys = ["collection_title", "title", "subtitle"]
        missing_keys = [key for key in required_keys if key not in video_info]
        if missing_keys:
            logger.warning(f"Missing required keys: {', '.join(missing_keys)}")
            # Provide default values for missing keys
            for key in missing_keys:
                video_info[key] = f"Default {key.replace('_', ' ').title()}"

        # Check if 'global_props.mp4' is already in the order array
        if "order" in video_info and "global_props.mp4" not in video_info["order"]:
            video_info["order"].insert(0, "global_props.mp4")
        elif "order" not in video_info:
            video_info["order"] = ["global_props.mp4"]

        # Create the new intro timestamp
        intro_timestamp = {"text": "Introduction", "time": "00:00:00", "duration": 10}

        # Check if the Introduction timestamp already exists
        if "timestamps" in video_info:
            if not any(
                ts["text"] == "Introduction" and ts["time"] == "00:00:00"
                for ts in video_info["timestamps"]
            ):
                video_info["timestamps"].insert(0, intro_timestamp)

                # Adjust all other timestamps by adding 10 seconds
                for timestamp in video_info["timestamps"][1:]:
                    time_parts = timestamp["time"].split(":")
                    hours = int(time_parts[0])
                    minutes = int(time_parts[1])
                    seconds = int(time_parts[2])

                    total_seconds = hours * 3600 + minutes * 60 + seconds + 10
                    new_hours = total_seconds // 3600
                    new_minutes = (total_seconds % 3600) // 60
                    new_seconds = total_seconds % 60

                    timestamp["time"] = (
                        f"{new_hours:02d}:{new_minutes:02d}:{new_seconds:02d}"
                    )
        else:
            video_info["timestamps"] = [intro_timestamp]

        # Add or update the 'transcript' array
        if "transcript" not in video_info:
            video_info["transcript"] = []

        # Combine collection title, title, and subtitle
        combined_text = f"{video_info['collection_title']}. {video_info['title']}. {video_info['subtitle']}"

        # Create new transcript item (without timestamp)
        new_transcript_item = {"text": combined_text}
        # Append the new item to the transcript array
        video_info["transcript"].append(new_transcript_item)

    except Exception as e:
        logger.error(f"Unexpected error in prepend_intro_timestamp: {str(e)}")
        logger.error(traceback.format_exc())
        raise

    return video_info


def process_urls(base_folder_url, layout_settings_path):
    try:
        # Ensure the base_folder_url ends with a trailing slash
        if not base_folder_url.endswith("/"):
            base_folder_url += "/"

        # Construct the full URL for the global_props.json
        global_props_url = base_folder_url + "global_props.json"

        logger.info(f"Fetching global_props.json from: {global_props_url}")
        response = requests.get(global_props_url)
        response.raise_for_status()
        video_info = response.json()

        # Process the single global_props.json
        process_single_url(video_info, base_folder_url, layout_settings_path)

    except requests.RequestException as e:
        logger.error(f"Failed to fetch or process URL: {str(e)}")
    except json.JSONDecodeError:
        logger.error(f"Failed to parse JSON from {global_props_url}")

    logger.info("Processing completed")


def get_upload_url(download_url):
    if download_url.startswith("http://localbrowse"):
        return "http://localbrowse/Users/bpenn/ExpectancyLearning/flask_apps/_util_scripts/video_intro_upload.php"
    elif download_url.startswith("https://chameleon.sdiclarity.com/"):
        return "https://chameleon.sdiclarity.com/flask_apps/_util_scripts/video_intro_upload.php"
    elif download_url.startswith("http://127.0.0.1:5000/"):
        logger.warning(
            "Using 'http://127.0.0.1:5000/' is not recommended. Please use 'http://localbrowse' for local development."
        )
        raise ValueError(
            "Invalid URL for local development. Use 'http://localbrowse' instead."
        )
    else:
        logger.error(f"Unknown download URL: {download_url}")
        raise ValueError(f"Unknown download URL: {download_url}")


def upload_file(file_path, upload_url, relative_dir, app_folder):
    with open(file_path, "rb") as file:
        files = {"file": file}
        data = {"directory": relative_dir, "app_folder": app_folder}
        try:
            response = requests.post(upload_url, files=files, data=data)
            response.raise_for_status()
            logger.info(f"Successfully uploaded {file_path}")
            return response
        except requests.RequestException as e:
            logger.error(f"Failed to upload {file_path}: {str(e)}")
            return None

def process_single_url(video_info, base_folder_url, layout_settings_path):
    logger.info(f"Processing data from: {base_folder_url}")
    try:
        logger.info(f"Successfully fetched JSON data. Keys present: {', '.join(video_info.keys())}")

        output_dir = os.getcwd()  # or specify a different output directory
        project_name, base_filename = create_presentation(video_info, layout_settings_path, output_dir, base_folder_url)
        logger.info(f"Received from create_presentation. project_name: {project_name}, base_filename: {base_filename}")

        # Get upload URL based on the download URL
        try:
            upload_url = get_upload_url(base_folder_url)
        except ValueError as e:
            logger.error(f"Critical error: {str(e)}")
            return

        # Extract relative directory and app folder from base_folder_url
        url_parts = base_folder_url.split('/')
        if base_folder_url.startswith("http://localbrowse"):
            # For local development using localbrowse
            exp_learning_index = url_parts.index('ExpectancyLearning')
            app_folder = url_parts[exp_learning_index + 2]  # Assuming 'flask_apps' is right after 'ExpectancyLearning'
            relative_dir = '/'.join(url_parts[exp_learning_index + 3:])
        elif 'flask_apps' in url_parts:
            # For production
            flask_apps_index = url_parts.index('flask_apps')
            app_folder = url_parts[flask_apps_index + 1]
            relative_dir = '/'.join(url_parts[flask_apps_index + 2:])
        else:
            logger.error(f"Unable to parse URL structure: {base_folder_url}")
            return

        logger.info(f"Parsed URL - app_folder: {app_folder}, relative_dir: {relative_dir}")

        # Upload created files
        files_to_upload = [
            f"{project_name}.pptx",
            f"{base_filename}.mp4",
            f"{base_filename}.json",
            "global_props.json"
        ]
        
        logger.info(f"Files to upload: {files_to_upload}")


        for filename in files_to_upload:
            file_path = os.path.join(output_dir, "remote_projects", project_name, filename)
            if os.path.exists(file_path):
                upload_path = os.path.join(app_folder, relative_dir, filename)
                logger.info(f"Attempting to upload {filename} to {upload_path}")
                upload_result = upload_file(file_path, upload_url, relative_dir, app_folder)
                if upload_result:
                    logger.info(f"Successfully uploaded {filename} to {upload_url}")
                else:
                    logger.error(f"Failed to upload {filename}")
            else:
                logger.warning(f"File not found for upload: {file_path}")

                
    except Exception as e:
        logger.error(f"Failed to process data from {base_folder_url}: {str(e)}")
        logger.error(traceback.format_exc())
    
    logger.info(f"Completed processing for: {base_folder_url}")

def download_file(url, filename, project_dir):
    try:
        response = requests.get(url)
        response.raise_for_status()
        local_path = os.path.join(project_dir, filename)
        with open(local_path, "wb") as f:
            f.write(response.content)
        logger.info(f"Successfully downloaded file from {url} to {local_path}")
        return local_path
    except requests.RequestException as e:
        logger.error(f"Failed to download file from {url}: {str(e)}")
        return None


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)

    print("Welcome to the Batch Video Intro Creator!")
    print("Enter 'l' for r processing or 'remote' for remote processing:")
    mode = input().strip().lower()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    layout_settings_path = os.path.join(script_dir, "layout_settings.json")

    if not os.path.exists(layout_settings_path):
        print(
            f"Error: layout_settings.json not found in the script directory: {script_dir}"
        )
        logger.error(
            f"layout_settings.json not found in the script directory: {script_dir}"
        )
        sys.exit(1)

    if mode == "l":
        print("Please enter the path to the folder containing your JSON files:")
        input_folder = input().strip().strip("\"'")
        if not os.path.exists(input_folder):
            print(f"Error: The folder '{input_folder}' does not exist.")
            logger.error(f"Input folder does not exist: {input_folder}")
            sys.exit(1)
        process_folder(input_folder, layout_settings_path)
    elif mode == "r":
        print(
            "Please enter the URL of the JSON file (either a single global_props.json or a list of URLs):"
        )
        url_list_json = input().strip()

        try:
            process_urls(url_list_json, layout_settings_path)
        except SystemExit:
            logger.info(
                "Script exited due to a critical error. Check the log for details."
            )
            print("Script exited due to a critical error. Check the log for details.")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            logger.error(traceback.format_exc())
            print("An unexpected error occurred. Check the log for details.")

    else:
        print(
            "Invalid mode selected. Please run the script again and choose 'local' or 'remote'."
        )
        sys.exit(1)

    print("Batch processing completed. Check the log for details.")

# http://127.0.0.1:5000/static/video_library/Labeler_Operation_Startup_and_Testing
