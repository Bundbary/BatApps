import os
import subprocess
import sys
import re

def get_video_duration(file_path):
    """Get the duration of the video in seconds using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return float(result.stdout.strip())

def get_total_frames(file_path):
    """Get the total number of frames in the video using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=nb_frames", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    return int(result.stdout.strip())

def get_video_frame_rate(file_path):
    """Get the frame rate of the video using ffprobe."""
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    # The frame rate might come as a fraction like '30000/1001', so we need to evaluate it
    frame_rate_str = result.stdout.strip()
    try:
        frame_rate = eval(frame_rate_str)
    except Exception:
        frame_rate = float(frame_rate_str)
    return frame_rate


def merge_videos(intro_file, main_file, output_file):
    """Merge the intro and main video with a fade effect and show percentage progress."""
    intro_duration = get_video_duration(intro_file)
    intro_framerate = get_video_frame_rate(intro_file)

    # Calculate total frames
    intro_frames = get_total_frames(intro_file)
    main_frames = get_total_frames(main_file)
    total_frames = intro_frames + main_frames

    fade_start = intro_duration - 1

    filter_complex = (
        f"[0:v]fps={intro_framerate},scale=1920:1080,"
        f"fade=t=out:st={fade_start}:d=1[v0];"
        f"[1:v]fps={intro_framerate},fade=t=in:st=0:d=1[v1];"
        f"[v0][0:a][v1][1:a]concat=n=2:v=1:a=1[outv][outa]"
    )

    command = [
        "ffmpeg", "-y",
        "-i", intro_file,
        "-i", main_file,
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "superfast",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_file
    ]

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # Regular expression to match the frame number in the FFmpeg output
    frame_regex = re.compile(r"frame=\s*(\d+)")

    for line in process.stdout:
        sys.stdout.write(line)
        sys.stdout.flush()

        # Check if the current line contains frame information
        match = frame_regex.search(line)
        if match:
            current_frame = int(match.group(1))
            progress = (current_frame / total_frames) * 100
            sys.stdout.write(f"\rProgress: {progress:.2f}%")
            sys.stdout.flush()

    process.wait()

    if process.returncode == 0:
        print(f"\nMerged: {intro_file} and {main_file} into {output_file}")
    else:
        print(f"\nError merging: {intro_file} and {main_file}")

def process_folder(folder_path):
    """Recursively process the folders and merge videos."""
    for root, dirs, files in os.walk(folder_path):
        # Skip 'backup' folders
        if 'backup' in root.lower():
            print(f"Skipping backup folder: {root}")
            continue

        intro_file = os.path.join(root, "global_props.mp4")
        main_file = os.path.join(root, "output.mp4")
        output_file = os.path.join(root, "presentation.mp4")

        if os.path.exists(intro_file) and os.path.exists(main_file):
            merge_videos(intro_file, main_file, output_file)
        else:
            if not os.path.exists(intro_file):
                print(f"Skipping folder, global_props.mp4 not found: {root}")
            if not os.path.exists(main_file):
                print(f"Skipping folder, output.mp4 not found: {root}")

if __name__ == "__main__":
    input_folder = input("Enter the path to the root folder containing videos: ")
    if not os.path.exists(input_folder):
        print(f"The folder {input_folder} does not exist.")
        sys.exit(1)

    process_folder(input_folder)
    print("Video merging complete.")
