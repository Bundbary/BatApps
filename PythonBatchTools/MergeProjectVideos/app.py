import json
import os
import subprocess

def merge_videos(folder_path):
    json_file = os.path.join(folder_path, "global_props.json")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    clip_order = data['order']
    output_file = os.path.join(folder_path, "output.mp4")
    
    # Prepare the filter complex string
    filter_complex = ""
    for i, clip in enumerate(clip_order):
        input_file = os.path.join(folder_path, clip)
        filter_complex += f"[{i}:v:0][{i}:a:0]"
    filter_complex += f"concat=n={len(clip_order)}:v=1:a=1[outv][outa]"
    
    # Prepare the FFmpeg command
    cmd = ["ffmpeg"]
    for clip in clip_order:
        input_file = os.path.join(folder_path, clip)
        cmd.extend(["-i", input_file])
    cmd.extend([
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-c:a", "aac",
        "-b:a", "192k",
        "-movflags", "+faststart",
        output_file
    ])
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully merged videos. Output saved as {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while merging videos: {e}")

folder_path = input("Enter the path to the folder containing the videos and global_props.json: ")
merge_videos(folder_path)