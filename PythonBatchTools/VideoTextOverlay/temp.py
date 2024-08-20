import json
from typing import List, Union
from dataclasses import dataclass
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.video.fx.all import fadeout, fadein
import numpy as np
import os
import subprocess
from moviepy.config import change_settings

# Set the path to ImageMagick binary
# Adjust this path to match your ImageMagick installation directory
imagemagick_binary = r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
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

    def is_dynamic_position(self) -> bool:
        return isinstance(self.position[0], str) and self.position[0].startswith("lambda")

    def is_rotating(self) -> bool:
        return self.rotate is not None and isinstance(self.rotate[0], str) and self.rotate[0].startswith("lambda")

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

    def apply_text_overlay(self, overlay: TextOverlay, video_size: tuple) -> TextClip:
        text_clip = TextClip(overlay.text, fontsize=overlay.fontsize, color=overlay.color, font='Arial', method='label')

        if overlay.is_dynamic_position():
            position_func = eval(overlay.position[0])
            text_clip = text_clip.set_position(position_func)
        else:
            text_clip = text_clip.set_position(tuple(overlay.position))

        text_clip = text_clip.set_duration(overlay.duration).set_start(overlay.start_time)

        if overlay.effect == "fade_in" and overlay.effect_duration:
            text_clip = text_clip.fx(fadein, duration=overlay.effect_duration)
        elif overlay.effect == "fade_out" and overlay.effect_duration:
            text_clip = text_clip.fx(fadeout, duration=overlay.effect_duration)

        if overlay.shadow_color and overlay.shadow_offset:
            shadow = TextClip(overlay.text, fontsize=overlay.fontsize, color=overlay.shadow_color, font='Arial', method='label')
            shadow = shadow.set_position((overlay.position[0] + overlay.shadow_offset[0],
                                          overlay.position[1] + overlay.shadow_offset[1]))
            text_clip = CompositeVideoClip([shadow, text_clip])

        if overlay.is_rotating():
            rotate_func = eval(overlay.rotate[0])
            text_clip = text_clip.rotate(lambda t: rotate_func(t))

        # Ensure the final clip has an alpha channel
        def ensure_alpha(frame):
            if frame.shape[2] == 3:
                return np.dstack((frame, np.ones((frame.shape[0], frame.shape[1], 1))))
            return frame

        text_clip = text_clip.fl_image(ensure_alpha)

        return text_clip

    def create_text_overlay_video(self) -> str:
        with VideoFileClip(self.video_path) as video:
            width, height = video.w, video.h
            duration = video.duration
            fps = video.fps

        # Create a transparent background
        background = ColorClip(size=(width, height), color=(0,0,0,0))
        background = background.set_duration(duration)

        text_clips = []
        for overlay in self.text_overlays:
            text_clip = self.apply_text_overlay(overlay, (width, height))
            text_clips.append(text_clip)

        # Composite all clips
        text_composite = CompositeVideoClip([background] + text_clips, size=(width, height))
        text_composite = text_composite.set_duration(duration)

        overlay_path = self.video_path.rsplit('.', 1)[0] + '_text_overlay.mp4'
        text_composite.write_videofile(overlay_path, fps=fps, codec='libx264', audio=False,
                                       ffmpeg_params=["-pix_fmt", "yuva420p", "-crf", "23"])

        return overlay_path

    def merge_videos(self, original_video: str, overlay_video: str, output_video: str):
        cmd = [
            "ffmpeg",
            "-i", original_video,
            "-i", overlay_video,
            "-filter_complex", "[1:v]format=rgba,colorchannelmixer=aa=1[ovr];[0:v][ovr]overlay=format=auto,format=yuv420p",
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-c:a", "copy",
            output_video,
        ]
        subprocess.run(cmd, check=True)

    def optimize_video(self, input_video: str, output_video: str):
        cmd = [
            "ffmpeg",
            "-i", input_video,
            "-c:v", "libx264",
            "-crf", "23",
            "-preset", "medium",
            "-c:a", "aac",
            "-b:a", "128k",
            output_video,
        ]
        subprocess.run(cmd, check=True)

    def process_overlays(self) -> None:
        overlay_video = self.create_text_overlay_video()
        merged_video = self.video_path.rsplit(".", 1)[0] + "_merged.mp4"
        self.merge_videos(self.video_path, overlay_video, merged_video)

        output_path = self.video_path.rsplit(".", 1)[0] + "_with_text_optimized.mp4"
        self.optimize_video(merged_video, output_path)

        # Clean up intermediate files
        os.remove(overlay_video)
        os.remove(merged_video)

def main():
    processor = VideoTextOverlayProcessor(
        r"c:\Users\bpenn\ExpectancyLearning\BatApps\PythonBatchTools\VideoTextOverlay\video_temp\video_temp.json"
    )
    processor.load_json_data()
    processor.process_overlays()

if __name__ == "__main__":
    main()