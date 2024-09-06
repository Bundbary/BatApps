import os
import json
import subprocess
from datetime import datetime, timezone
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key="sk--g2hiAUedCQ72Qk3DiAxxvKxkOEltseJThkuGGWCnCT3BlbkFJEoOjLUoOD1CCWxNlRMxF3-81c4FruygP7WruHdBocA")

def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
    return transcript.text

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

def create_json_object(label, transcript, duration):
    return {
        "label": label,
        "notes": [],
        "transcript": [
            {
                "text": transcript,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        ],
        "title": "",
        "text": "",
        "duration": duration
    }

def process_file(audio_path):
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    transcript_path = os.path.join(os.path.dirname(audio_path), f"{base_name}_transcript.txt")
    json_path = os.path.join(os.path.dirname(audio_path), f"{base_name}.json")

    if os.path.exists(transcript_path):
        print(f"Skipping {os.path.basename(audio_path)} (transcript already exists)")
        return

    print(f"Processing {os.path.basename(audio_path)}...")

    try:
        # Transcribe audio
        transcript = transcribe_audio(audio_path)

        # Get audio duration
        duration = get_video_duration(audio_path)

        # Save transcript as text file
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        # Create and save JSON file
        json_object = create_json_object(base_name, transcript, duration)
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(json_object, f, indent=2, ensure_ascii=False)

        print(f"Transcription and JSON saved for {os.path.basename(audio_path)}")
    except Exception as e:
        print(f"Error processing {os.path.basename(audio_path)}: {str(e)}")

def process_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        # Remove '_backup' from dirs to skip it
        if '_backup' in dirs:
            dirs.remove('_backup')

        for filename in files:
            if filename.endswith(".mp3"):
                audio_path = os.path.join(root, filename)
                process_file(audio_path)

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing MP3 files: ")
    print(f"Processing folder: {folder_path}")
    process_folder(folder_path)