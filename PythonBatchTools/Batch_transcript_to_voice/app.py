import os
from pathlib import Path
import requests
import json
import re
import subprocess
import shutil

def sanitize_text(text):
    text = ''.join(char for char in text if char.isprintable())
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def get_transcript_from_json(json_file_path):
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        transcript_array = data.get('transcript', [])
        if transcript_array:
            return transcript_array[-1].get('text', '')
    except Exception as e:
        print(f"Error reading transcript from {json_file_path}: {str(e)}")
    
    return ''  # Return empty string instead of None

def add_audio_to_video(video_path, audio_path, output_path):
    try:
        command = [
            'ffmpeg',
            '-i', str(video_path),
            '-i', str(audio_path),
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-map', '0:v:0',
            '-map', '1:a:0',
            '-shortest',
            '-y',  # Overwrite output file if it exists
            str(output_path)
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully added audio to video: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error adding audio to video: {e}")
        print(f"FFmpeg stdout: {e.stdout}")
        print(f"FFmpeg stderr: {e.stderr}")
        return False

def remove_audio_from_video(video_path, output_path):
    try:
        command = [
            'ffmpeg',
            '-i', str(video_path),
            '-c:v', 'copy',
            '-an',
            '-y',  # Overwrite output file if it exists
            str(output_path)
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"Successfully removed audio from video: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error removing audio from video: {e}")
        print(f"FFmpeg stdout: {e.stdout}")
        print(f"FFmpeg stderr: {e.stderr}")
        return False

def process_folder(folder_path, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    global_props_path = Path(folder_path) / 'global_props.json'
    
    if global_props_path.exists():
        try:
            with open(global_props_path, 'r', encoding='utf-8') as f:
                global_props = json.load(f)
            
            order = global_props.get('order', [])
        except Exception as e:
            print(f"Error reading global_props.json in {folder_path}: {str(e)}")
            return
    else:
        print(f"No global_props.json found in {folder_path}. Skipping this folder.")
        return

    backup_folder = Path(folder_path) / '_backups'
    backup_folder.mkdir(exist_ok=True)

    for mp4_file in order:
        mp4_path = Path(folder_path) / mp4_file
        json_file = Path(folder_path) / f"{Path(mp4_file).stem}.json"
        audio_file = Path(folder_path) / f"{Path(mp4_file).stem}_temp_audio.mp3"
        temp_output_video = Path(folder_path) / f"{Path(mp4_file).stem}_temp.mp4"

        if not mp4_path.exists():
            print(f"Warning: {mp4_file} not found in {folder_path}. Skipping.")
            continue

        transcript_text = get_transcript_from_json(json_file)
        
        try:
            if not transcript_text:
                print(f"No text found for {mp4_file}. Removing existing audio.")
                if remove_audio_from_video(mp4_path, temp_output_video):
                    print(f"Successfully processed {mp4_file} (removed audio)")
                else:
                    print(f"Failed to remove audio from {mp4_file}")
                    continue
            else:
                sanitized_text = sanitize_text(transcript_text)
                print(f"Processing file: {mp4_file}")
                print(f"Text content (first 100 chars): {sanitized_text[:100]}...")

                max_chars = 250  # Free tier limit
                if len(sanitized_text) > max_chars:
                    print(f"Text too long ({len(sanitized_text)} chars). Truncating to {max_chars} chars.")
                    sanitized_text = sanitized_text[:max_chars]

                payload = {
                    "Engine": "neural",
                    "VoiceId": "ai3-Jony",
                    "LanguageCode": "en-US",
                    "Text": sanitized_text,
                    "OutputFormat": "mp3",
                    "SampleRate": "48000",
                    "Effect": "default",
                    "MasterVolume": "0",
                    "MasterSpeed": "0",
                    "MasterPitch": "0"
                }

                response = requests.post("https://developer.voicemaker.in/voice/api", headers=headers, json=payload)
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        audio_url = result['path']
                        print(f"Audio generated. Downloading from: {audio_url}")
                        audio_response = requests.get(audio_url)
                        with open(audio_file, 'wb') as f:
                            f.write(audio_response.content)
                        print(f"Generated MP3 for {mp4_file}")

                        # Add audio to video
                        if not add_audio_to_video(mp4_path, audio_file, temp_output_video):
                            print(f"Failed to add audio to {mp4_file}")
                            continue
                    else:
                        print(f"API returned success=false. Message: {result.get('message')}")
                        if "character limit" in result.get('message', '').lower():
                            print("You have reached your character limit. Please recharge your account at Voicemaker.")
                            return  # Stop processing further files
                else:
                    print(f"API request failed with status code: {response.status_code}")
                    print(f"Response content: {response.text}")
                    if response.status_code == 400 and "character limit" in response.text.lower():
                        print("You have reached your character limit. Please recharge your account at Voicemaker.")
                        return  # Stop processing further files

            # Move original file to backup folder
            backup_path = backup_folder / mp4_file
            shutil.move(str(mp4_path), str(backup_path))
            print(f"Moved original file to: {backup_path}")

            # Rename temp file to original name
            os.rename(temp_output_video, mp4_path)
            print(f"Renamed processed file to: {mp4_path}")

            # Remove temporary audio file if it exists
            if audio_file.exists():
                os.remove(audio_file)
                print(f"Removed temporary audio file: {audio_file}")

        except Exception as e:
            print(f"Error processing {mp4_file}: {str(e)}")

def process_files_recursively(root_folder, api_key):
    for folder_path, subfolders, files in os.walk(root_folder):
        # Remove folders with 'backup' in the name from subfolders list
        subfolders[:] = [d for d in subfolders if 'backup' not in d.lower()]

        print(f"Processing folder: {folder_path}")
        process_folder(folder_path, api_key)

if __name__ == "__main__":
    root_folder = input("Enter the root folder path: ")
    api_key = "9c73f0e0-6e14-11ef-9d35-2ff8558a697f"
    process_files_recursively(root_folder, api_key)