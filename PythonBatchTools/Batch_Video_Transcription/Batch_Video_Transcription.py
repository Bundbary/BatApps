import os
from moviepy.editor import VideoFileClip
from openai import OpenAI

# Initialize the OpenAI client
client = OpenAI(api_key="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")


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
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724072039_0007_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724072454_0008_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724075151_0010_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724075553_0011_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724080905_0012_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724081304_0013_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724085056_0014_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724085421_0015_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724085610_0016_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724085718_0017_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724090112_0018_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724091545_0019_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724091711_0020_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724091947_0021_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724093843_0022_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724094314_0023_D_clips",
        "c:\\Users\\bpenn\\ExpectancyLearning\\Reckitt\\Video\\JeremyNarratedPrimary\\mp4\\clips\\all_video_clips\\DJI_20240724095037_0024_D_clips",
    ]

    for folder_path in sample_folder_paths:
        process_folder(folder_path)
    folder_path = input("Enter the path to the folder containing MP4 files: ")
