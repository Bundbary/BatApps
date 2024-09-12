import json
import os
import subprocess
import tempfile

def merge_videos(folder_path):
    # Construct the full path to the JSON file
    json_file = os.path.join(folder_path, "global_props.json")
    
    # Read the JSON file
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Get the order of clips from the JSON
    clip_order = data['order']
    
    # Output file path
    output_file = os.path.join(folder_path, "output.mp4")
    
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix='.txt') as temp_file:
        for clip in clip_order:
            temp_file.write(f"file '{os.path.join(folder_path, clip)}'\n")
        temp_file_name = temp_file.name

    try:
        # FFmpeg command
        cmd = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", temp_file_name,
            "-c", "copy",
            output_file
        ]
        
        # Run FFmpeg command
        subprocess.run(cmd, check=True)
        print(f"Successfully merged videos. Output saved as {output_file}")
    except subprocess.CalledProcessError as e:
        print(f"An error occurred while merging videos: {e}")
    finally:
        # Clean up the temporary file
        os.unlink(temp_file_name)

# Get user input for the folder path
folder_path = input("Enter the path to the folder containing the videos and global_props.json: ")

# Use the function
merge_videos(folder_path)