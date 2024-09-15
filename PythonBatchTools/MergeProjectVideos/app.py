import json
import os
import subprocess

def merge_videos(folder_path):
    json_file = os.path.join(folder_path, "global_props.json")
    
    if not os.path.exists(json_file):
        print(f"No global_props.json found in {folder_path}. Skipping.")
        return

    with open(json_file, 'r') as f:
        data = json.load(f)
    
    clip_order = data.get('order', [])
    error_clips = data.get('error_clips', [])
    output_file = os.path.join(folder_path, "output.mp4")
    
    valid_clips = []
    new_error_clips = []

    for clip in clip_order:
        input_file = os.path.join(folder_path, clip)
        try:
            # Try to get some basic info about the file using ffprobe
            cmd = [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-count_packets",
                "-show_entries", "stream=nb_read_packets",
                "-of", "csv=p=0",
                input_file
            ]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            valid_clips.append(clip)
        except subprocess.CalledProcessError as e:
            print(f"Error processing file: {input_file}")
            new_error_clips.append({'clip': clip, 'error': str(e)})
        except Exception as e:
            print(f"Unexpected error with file: {input_file}")
            new_error_clips.append({'clip': clip, 'error': str(e)})

    if not valid_clips:
        print("No valid input files found. Skipping merge.")
        return
    
    # Update global_props.json
    data['order'] = valid_clips
    data['error_clips'] = error_clips + new_error_clips
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    # Prepare the filter complex string
    filter_complex = ""
    for i, clip in enumerate(valid_clips):
        filter_complex += f"[{i}:v:0][{i}:a:0]"
    filter_complex += f"concat=n={len(valid_clips)}:v=1:a=1[outv][outa]"
    
    # Prepare the FFmpeg command
    cmd = ["ffmpeg", "-y"]  # Force overwrite
    for clip in valid_clips:
        input_file = os.path.join(folder_path, clip)
        cmd.extend(["-i", input_file])
    cmd.extend([
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
    ])
    
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully merged videos. Output saved as {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while merging videos: {e}")
        print(f"FFmpeg command: {' '.join(cmd)}")

def process_folders(root_folder):
    for folder_name, subfolders, files in os.walk(root_folder):
        if 'backup' in folder_name.lower():
            print(f"Skipping backup folder: {folder_name}")
            continue
        
        if "global_props.json" in files:
            print(f"Processing folder: {folder_name}")
            try:
                merge_videos(folder_name)
            except Exception as e:
                print(f"Error processing folder {folder_name}: {e}")
                
if __name__ == "__main__":
    root_folder = input("Enter the root folder path to start processing: ")
    process_folders(root_folder)