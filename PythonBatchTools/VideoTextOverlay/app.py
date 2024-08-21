import json
import math
import numpy as np
import re
import os
from typing import List, Union, Callable
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip, VideoClip
from moviepy.video.tools.segmenting import findObjects
from moviepy.video.fx.all import fadeout, fadein
from skimage import transform as tf
from moviepy.config import change_settings

# Set the path to ImageMagick binary
imagemagick_binary = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
change_settings({"IMAGEMAGICK_BINARY": imagemagick_binary})

def color_to_rgb(color_string):
    """Convert color string to RGB tuple."""
    if isinstance(color_string, tuple):
        return color_string
    if color_string.startswith('#'):
        # Hex color
        return tuple(int(color_string[i:i+2], 16) for i in (1, 3, 5))
    elif color_string.startswith('rgb'):
        # RGB color
        return tuple(map(int, re.findall(r'\d+', color_string)))
    else:
        # Named color (limited set for simplicity)
        colors = {
            'white': (255, 255, 255),
            'black': (0, 0, 0),
            'red': (255, 0, 0),
            'green': (0, 255, 0),
            'blue': (0, 0, 255),
            # Add more colors as needed
        }
        return colors.get(color_string.lower(), (0, 0, 0))  # Default to black if color not found

@dataclass
class TextOverlay:
    text: str
    fontsize: int
    color: Union[str, List[str]]
    position: Union[List[int], List[str]]
    duration: float
    start_time: float
    effect: str = None
    effect_duration: float = None
    rotate: List[str] = None
    fontsize_function: List[str] = None
    perspective: List[float] = None
    scroll_speed: float = None
    animate_letters: bool = False
    background_color: str = None
    background_opacity: float = None

    def is_dynamic_position(self) -> bool:
        return isinstance(self.position[0], str) and self.position[0].startswith("lambda")

    def is_rotating(self) -> bool:
        return self.rotate is not None and isinstance(self.rotate[0], str) and self.rotate[0].startswith("lambda")

    def is_dynamic_color(self) -> bool:
        return isinstance(self.color, list) and self.color[0].startswith("lambda")

    def is_dynamic_fontsize(self) -> bool:
        return self.fontsize_function is not None and self.fontsize_function[0].startswith("lambda")

class VideoTextOverlayProcessor:
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.video_path = ""
        self.text_overlays: List[TextOverlay] = []

    def load_json_data(self) -> None:
        with open(self.json_file_path, "r") as file:
            data = json.load(file)
            self.video_path = data.get("video_path", "")
            self.text_overlays = [TextOverlay(**item) for item in data.get("text_data", [])]

    def apply_text_overlay(self, overlay: TextOverlay, video_size: tuple) -> VideoClip:
        def create_text_clip(t):
            current_fontsize = overlay.fontsize
            if overlay.fontsize_function:
                fontsize_func = eval(overlay.fontsize_function[0])
                current_fontsize = int(fontsize_func(t))

            current_color = overlay.color
            if isinstance(overlay.color, list):
                color_func = eval(overlay.color[0])
                current_color = color_func(t)

            # Ensure color is in the correct format
            if isinstance(current_color, tuple):
                current_color = 'rgb' + str(current_color)
            elif not isinstance(current_color, str):
                current_color = str(current_color)

            text_clip = TextClip(str(overlay.text), fontsize=current_fontsize, color=current_color, font='Arial', method='label')
            
            if overlay.animate_letters:
                letters = findObjects(text_clip)
                letter_clips = [letter.set_position(lambda t: (letter.screenpos[0], letter.screenpos[1] + np.sin(t*5 + i*0.5)*10)) 
                                for i, letter in enumerate(letters)]
                text_clip = CompositeVideoClip(letter_clips, size=text_clip.size)

            if overlay.background_color:
                bg_color = color_to_rgb(overlay.background_color)
                bg_color_str = 'rgb' + str(bg_color)
                text_clip = text_clip.on_color(
                    size=(text_clip.w + 10, text_clip.h + 10),
                    color=bg_color_str,
                    pos=(5, 'center'),
                    col_opacity=overlay.background_opacity or 1
                )

            if overlay.perspective:
                text_clip = text_clip.image_transform(
                    lambda pic: self.apply_perspective(pic, *overlay.perspective))

            return text_clip
        
        def make_frame(t):
            return create_text_clip(t).get_frame(t)

        text_clip = VideoClip(make_frame=make_frame, duration=overlay.duration)
        
        if isinstance(overlay.position[0], str):
            position_func = eval(overlay.position[0])
            text_clip = text_clip.set_position(position_func)
        elif overlay.scroll_speed:
            text_clip = text_clip.set_position(lambda t: (text_clip.w/2, video_size[1] + t * overlay.scroll_speed))
        else:
            text_clip = text_clip.set_position(tuple(overlay.position))

        text_clip = text_clip.set_start(overlay.start_time)

        if overlay.effect == "fade_in" and overlay.effect_duration:
            text_clip = text_clip.fx(fadein, duration=overlay.effect_duration)
        elif overlay.effect == "fade_out" and overlay.effect_duration:
            text_clip = text_clip.fx(fadeout, duration=overlay.effect_duration)

        if overlay.rotate:
            rotate_func = eval(overlay.rotate[0])
            text_clip = text_clip.rotate(lambda t: rotate_func(t))

        return text_clip

    @staticmethod
    def apply_perspective(pic, cx, cy):
        Y, X = pic.shape[:2]
        src = np.array([[0, 0], [X, 0], [X, Y], [0, Y]])
        dst = np.array([[cx * X, cy * Y], [(1 - cx) * X, cy * Y], [X, Y], [0, Y]])
        tform = tf.ProjectiveTransform()
        tform.estimate(src, dst)
        return tf.warp(pic, tform.inverse, output_shape=(Y, X))

    def create_text_overlay_video(self) -> str:
        with VideoFileClip(self.video_path) as video:
            width, height = video.w, video.h
            duration = video.duration
            fps = video.fps

        # Create a transparent background
        background = ColorClip(size=(width, height), color=(0, 0, 0, 0)).set_duration(duration)

        text_clips = []
        for i, overlay in enumerate(self.text_overlays):
            try:
                text_clip = self.apply_text_overlay(overlay, (width, height))
                if text_clip is None:
                    print(f"Warning: text_clip for overlay {i} is None")
                else:
                    print(f"Created text_clip for overlay {i}: duration={text_clip.duration}, size={text_clip.size}")
                    text_clips.append(text_clip)
            except Exception as e:
                print(f"Error creating text_clip for overlay {i}: {str(e)}")

        # Filter out None clips
        text_clips = [clip for clip in text_clips if clip is not None]

        if not text_clips:
            print("Warning: No valid text clips were created.")
            return None

        # Composite all clips
        try:
            text_composite = CompositeVideoClip([background] + text_clips, size=(width, height))
            text_composite = text_composite.set_duration(duration)
        except Exception as e:
            print(f"Error creating CompositeVideoClip: {str(e)}")
            return None

        overlay_path = os.path.splitext(self.video_path)[0] + "_text_overlay.mp4"
        text_composite.write_videofile(
            overlay_path,
            fps=fps,
            codec="libx264",
            ffmpeg_params=["-pix_fmt", "yuva420p", "-crf", "23"],
        )

        return overlay_path

    def process_overlays(self) -> None:
        self.create_text_overlay_video()

def main():
    processor = VideoTextOverlayProcessor(
        r"c:\Users\bpenn\ExpectancyLearning\BatApps\PythonBatchTools\VideoTextOverlay\video_temp\video_temp.json"
    )
    processor.load_json_data()
    processor.process_overlays()

if __name__ == "__main__":
    main()