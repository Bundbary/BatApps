import os
from pathlib import Path
import requests
import json
import re
import subprocess

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

def process_folder(folder_path, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    global_props_path = Path(folder_path) / 'global_props.json'
    mp4_path = Path(folder_path) / 'global_props.mp4'
    
    if not global_props_path.exists() or not mp4_path.exists():
        print(f"Missing global_props.json or global_props.mp4 in {folder_path}. Skipping this folder.")
        return

    try:
        transcript_text = get_transcript_from_json(global_props_path)
        
        if not transcript_text:
            print(f"No transcript found in global_props.json. Skipping this folder.")
            return

        sanitized_text = sanitize_text(transcript_text)
        print(f"Processing file: global_props.mp4")
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
        
        if response.status_code != 200:
            print(f"API request failed with status code: {response.status_code}")
            print(f"Response content: {response.text}")
            return

        result = response.json()
        if not result.get('success'):
            print(f"API returned success=false. Message: {result.get('message')}")
            return

        audio_url = result['path']
        print(f"Audio generated. Downloading from: {audio_url}")
        
        audio_file = Path(folder_path) / "temp_audio.mp3"
        temp_output_video = Path(folder_path) / "temp_output.mp4"

        audio_response = requests.get(audio_url)
        with open(audio_file, 'wb') as f:
            f.write(audio_response.content)

        if not add_audio_to_video(mp4_path, audio_file, temp_output_video):
            print(f"Failed to add audio to global_props.mp4. Skipping this folder.")
            if audio_file.exists():
                os.remove(audio_file)
            if temp_output_video.exists():
                os.remove(temp_output_video)
            return

        # Replace the original file with the new one
        os.remove(mp4_path)
        os.rename(temp_output_video, mp4_path)
        print(f"Replaced original file with new audio-added version: {mp4_path}")

        # Remove temporary audio file
        os.remove(audio_file)
        print(f"Removed temporary audio file: {audio_file}")

    except Exception as e:
        print(f"Error processing global_props.mp4: {str(e)}")
        print("The original file may have been modified. Please check the output.")
        # Clean up any temporary files that might have been created
        audio_file = Path(folder_path) / "temp_audio.mp3"
        temp_output_video = Path(folder_path) / "temp_output.mp4"
        if audio_file.exists():
            os.remove(audio_file)
        if temp_output_video.exists():
            os.remove(temp_output_video)

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