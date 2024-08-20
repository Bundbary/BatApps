import json
from typing import List, Dict, Any, Union
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import fadeout, fadein
import numpy as np
from PIL import Image, ImageFilter, ImageColor
import os
from moviepy.config import change_settings

# Set the path to ImageMagick binary
# Adjust this path to match your ImageMagick installation directory
imagemagick_binary = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"

# Configure MoviePy to use the specified ImageMagick binary
change_settings({"IMAGEMAGICK_BINARY": imagemagick_binary})


@dataclass
class TextOverlay:
    text: str
    fontsize: int
    color: str
    position: Union[List[int], List[str]]
    duration: float
    start_time: float
    effect: str = None
    effect_duration: float = None
    shadow_color: str = None
    shadow_offset: List[int] = None
    rotate: List[str] = None
    glow_color: str = None
    glow_radius: int = None

    def is_dynamic_position(self) -> bool:
        return isinstance(self.position[0], str) and self.position[0].startswith(
            "lambda"
        )

    def is_rotating(self) -> bool:
        return (
            self.rotate is not None
            and isinstance(self.rotate[0], str)
            and self.rotate[0].startswith("lambda")
        )


class VideoTextOverlayProcessor:
    def __init__(self, json_file_path: str):
        self.json_file_path = json_file_path
        self.video_path = ""
        self.text_overlays: List[TextOverlay] = []
        self.video_clip = None

    def load_json_data(self) -> None:
        with open(self.json_file_path, "r") as file:
            data = json.load(file)
            self.video_path = data.get("video_path", "")
            self.text_overlays = [
                TextOverlay(**item) for item in data.get("text_data", [])
            ]


    def process_overlays(self) -> None:
        # Load video without audio
        self.video_clip = VideoFileClip(self.video_path, audio=False)
        text_clips = []

        for i, overlay in enumerate(self.text_overlays):
            print(f"Processing overlay {i+1}: {overlay.text}")
            print(f"Color: {overlay.color}, Glow Color: {overlay.glow_color}")
            try:
                text_clip = self.apply_text_overlay(overlay)
                text_clips.append(text_clip)
            except Exception as e:
                print(f"Error processing overlay {i+1}: {str(e)}")

        # Create a base clip with alpha channel
        base = ColorClip(size=self.video_clip.size, color=(0,0,0,0))
        base = base.set_duration(self.video_clip.duration)

        # Composite all text clips onto the base
        text_composite = CompositeVideoClip([base] + text_clips)

        # Create the final composite clip
        final_clip = CompositeVideoClip([self.video_clip, text_composite])
        
        # Set the duration of the final clip to match the video duration
        final_clip = final_clip.set_duration(self.video_clip.duration)

        output_path = self.video_path.rsplit('.', 1)[0] + '_with_text.mp4'
        final_clip.write_videofile(output_path, codec='mpeg4', fps=self.video_clip.fps, audio=False)


    def apply_glow(self, image, radius, color):
        # Convert MoviePy's numpy array to PIL Image
        pil_image = Image.fromarray((image * 255).astype('uint8')).convert('RGBA')
        
        # Convert color string to RGB
        try:
            if color.startswith('#'):
                rgb_color = tuple(int(color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
            else:
                rgb_color = ImageColor.getrgb(color)
        except ValueError:
            print(f"Invalid color '{color}'. Using default color (white).")
            rgb_color = (255, 255, 255)
        
        # Create a new image with the glow color
        glow = Image.new('RGBA', pil_image.size, rgb_color + (0,))
        
        # Paste the original image onto the glow image
        glow.paste(pil_image, (0, 0), pil_image)
        
        # Apply blur
        glow = glow.filter(ImageFilter.GaussianBlur(radius))
        
        # Composite the glow with the original image
        result = Image.alpha_composite(glow, pil_image)
        
        # Convert back to numpy array
        return np.array(result) / 255.0



    def apply_text_overlay(self, overlay: TextOverlay) -> TextClip:
        # Create base TextClip
        text_clip = TextClip(overlay.text, fontsize=overlay.fontsize, color=overlay.color, font='Arial', method='label')

        # Set position
        if overlay.is_dynamic_position():
            position_func = eval(overlay.position[0])
            text_clip = text_clip.set_position(position_func)
        else:
            text_clip = text_clip.set_position(tuple(overlay.position))

        # Set duration and start time
        text_clip = text_clip.set_duration(overlay.duration).set_start(overlay.start_time)

        # Apply effects
        if overlay.effect == "fade_in" and overlay.effect_duration:
            text_clip = text_clip.fx(fadein, duration=overlay.effect_duration)
        elif overlay.effect == "fade_out" and overlay.effect_duration:
            text_clip = text_clip.fx(fadeout, duration=overlay.effect_duration)

        # Apply shadow
        if overlay.shadow_color and overlay.shadow_offset:
            shadow = TextClip(overlay.text, fontsize=overlay.fontsize, color=overlay.shadow_color, font='Arial', method='label')
            shadow = shadow.set_position((overlay.position[0] + overlay.shadow_offset[0],
                                          overlay.position[1] + overlay.shadow_offset[1]))
            text_clip = CompositeVideoClip([shadow, text_clip])

        # Apply rotation
        if overlay.is_rotating():
            rotate_func = eval(overlay.rotate[0])
            text_clip = text_clip.rotate(lambda t: rotate_func(t))

        # Apply glow effect
        if overlay.glow_color and overlay.glow_radius:
            glow_func = lambda img: self.apply_glow(img, overlay.glow_radius, overlay.glow_color)
            text_clip = text_clip.fl_image(glow_func)

        # Ensure the clip has an alpha channel and is the same size as the video
        text_clip = text_clip.on_color(size=self.video_clip.size, color=(0,0,0,0), pos=text_clip.pos, col_opacity=0)

        return text_clip


def main():
    processor = VideoTextOverlayProcessor(
        r"c:\Users\bpenn\ExpectancyLearning\BatApps\PythonBatchTools\VideoTextOverlay\video_temp\video_temp.json"
    )
    processor.load_json_data()
    processor.process_overlays()


if __name__ == "__main__":
    main()
