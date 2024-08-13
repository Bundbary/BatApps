import os
from moviepy.editor import VideoFileClip
from openai import OpenAI

import configparser

# Initialize the OpenAI client



def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    video.audio.write_audiofile(audio_path)


def transcribe_audio(audio_path):
    with open(audio_path, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            model="whisper-1", file=audio_file
        )
    return transcript.text


def process_folder(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".mp4"):
            video_path = os.path.join(folder_path, filename)
            base_name = os.path.splitext(filename)[0]
            audio_path = os.path.join(folder_path, f"{base_name}.mp3")
            transcript_path = os.path.join(folder_path, f"{base_name}_transcript.txt")

            print(f"Processing {filename}...")

            # Extract audio
            extract_audio(video_path, audio_path)

            # Transcribe audio
            try:
                transcript = transcribe_audio(audio_path)

                # Save transcript
                with open(transcript_path, "w") as f:
                    f.write(transcript)

                print(f"Transcription saved for {filename}")
            except Exception as e:
                print(f"Error transcribing {filename}: {str(e)}")

            print(f"Audio saved as {audio_path}")


if __name__ == "__main__":
    sample_folder_paths = [
        "c:\\11111\\test\\noaudio_videos"
    ]

    for folder_path in sample_folder_paths:
        print(f"Processing folder: {folder_path}")
        process_folder(folder_path)
    folder_path = input("Enter the path to the folder containing MP4 files: ")
