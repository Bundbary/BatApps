import os
import json
from datetime import datetime, timezone
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key="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")

def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
    return transcript.text

def create_json_object(label, transcript):
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
        "text": ""
    }

def process_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".mp3"):
            audio_path = os.path.join(folder_path, filename)
            base_name = os.path.splitext(filename)[0]
            transcript_path = os.path.join(folder_path, f"{base_name}_transcript.txt")
            json_path = os.path.join(folder_path, f"{base_name}.json")

            print(f"Processing {filename}...")

            try:
                # Transcribe audio
                transcript = transcribe_audio(audio_path)

                # Save transcript as text file
                with open(transcript_path, "w") as f:
                    f.write(transcript)

                # Create and save JSON file
                json_object = create_json_object(base_name, transcript)
                with open(json_path, "w") as f:
                    json.dump(json_object, f, indent=2)

                print(f"Transcription and JSON saved for {filename}")
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing MP3 files: ")
    print(f"Processing folder: {folder_path}")
    process_folder(folder_path)