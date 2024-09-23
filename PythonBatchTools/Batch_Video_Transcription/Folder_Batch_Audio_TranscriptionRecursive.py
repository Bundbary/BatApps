import os
import json
import subprocess
from datetime import datetime, timezone
from openai import OpenAI

# Initialize the OpenAI client with an API key
# Note: It's generally not recommended to hardcode API keys in scripts
client = OpenAI(api_key="sk--g2hiAUedCQ72Qk3DiAxxvKxkOEltseJThkuGGWCnCT3BlbkFJEoOjLUoOD1CCWxNlRMxF3-81c4FruygP7WruHdBocA")

def transcribe_audio(audio_path):
    """
    Transcribes an audio file using OpenAI's Whisper model.
    
    :param audio_path: Path to the audio file
    :return: Transcribed text
    """
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
    return transcript.text

def get_video_duration(video_path):
    """
    Gets the duration of a video file using ffprobe.
    
    :param video_path: Path to the video file
    :return: Duration in seconds, or None if an error occurs
    """
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
    """
    Creates a JSON object with the given information.
    
    :param label: Label for the JSON object (usually the filename)
    :param transcript: Transcribed text
    :param duration: Duration of the audio/video
    :return: Dictionary representing the JSON object
    """
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
    """
    Processes a single audio file: transcribes it, gets its duration,
    and saves the results as a text file and a JSON file.
    
    :param audio_path: Path to the audio file
    """
    # Extract the base name of the file (without extension)
    base_name = os.path.splitext(os.path.basename(audio_path))[0]
    
    # Define paths for the transcript and JSON files
    transcript_path = os.path.join(os.path.dirname(audio_path), f"{base_name}_transcript.txt")
    json_path = os.path.join(os.path.dirname(audio_path), f"{base_name}.json")

    # Skip if transcript already exists
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
    """
    Recursively processes all MP3 files in the given folder and its subfolders,
    skipping any folder named '_backup'.
    
    :param folder_path: Path to the root folder to process
    """
    for root, dirs, files in os.walk(folder_path):
        # Remove '_backup' from dirs to skip it
        if '_backup' in dirs:
            dirs.remove('_backup')

        for filename in files:
            if filename.endswith(".mp3"):
                audio_path = os.path.join(root, filename)
                process_file(audio_path)

if __name__ == "__main__":
    # Get the folder path from user input
    folder_path = input("Enter the path to the folder containing MP3 files: ")
    print(f"Processing folder: {folder_path}")
    # Start processing the folder
    process_folder(folder_path)