import os
import json
import subprocess

def get_video_duration(video_path):
    try:
        result = subprocess.run([
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting video duration: {e}")
        return None

def create_or_update_json(video_path, duration):
    base_name = os.path.splitext(os.path.basename(video_path))[0]
    json_path = os.path.join(os.path.dirname(video_path), f"{base_name}.json")
    
    if os.path.exists(json_path):
        # Update existing JSON file
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        data['duration'] = duration
    else:
        # Create new JSON file
        data = {
            "label": base_name,
            "notes": [],
            "transcript": [],
            "title": "",
            "text": "",
            "duration": duration
        }
    
    # Write updated or new JSON file
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        # Remove '_backups' from dirs to skip it
        if '_backups' in dirs:
            dirs.remove('_backups')
        
        for filename in files:
            if filename.endswith(".mp4"):
                video_path = os.path.join(root, filename)
                print(f"Processing {filename}...")
                
                duration = get_video_duration(video_path)
                if duration is not None:
                    create_or_update_json(video_path, duration)
                    print(f"Updated JSON for {filename}")
                else:
                    print(f"Failed to get duration for {filename}")

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing MP4 files: ")
    print(f"Processing folder: {folder_path}")
    process_folder(folder_path)