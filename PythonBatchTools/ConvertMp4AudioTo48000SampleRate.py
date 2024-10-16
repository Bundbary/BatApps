import os
import subprocess
import sys
import json
from pathlib import Path

def get_ffmpeg_path():
    ffmpeg_path = os.path.expanduser("~/bin/ffmpeg")
    return ffmpeg_path if os.path.exists(ffmpeg_path) else "ffmpeg"

def get_ffprobe_path():
    ffprobe_path = os.path.expanduser("~/bin/ffprobe")
    return ffprobe_path if os.path.exists(ffprobe_path) else "ffprobe"

def get_audio_info(file_path):
    ffprobe_path = get_ffprobe_path()
    cmd = [
        ffprobe_path,
        "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=sample_rate,channels",
        "-of", "json",
        file_path
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    info = json.loads(result.stdout)
    stream = info['streams'][0] if info['streams'] else {}
    return {
        'sample_rate': int(stream.get('sample_rate', 0)),
        'channels': int(stream.get('channels', 0))
    }

def convert_audio(input_path, output_path):
    ffmpeg_path = get_ffmpeg_path()
    cmd = [
        ffmpeg_path,
        "-i", input_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-ar", "48000",
        "-ac", "1",
        "-y",
        output_path
    ]
    subprocess.run(cmd, check=True)

def process_folder(folder_path):
    folder = Path(folder_path)
    if not folder.is_dir():
        print(f"Error: '{folder_path}' is not a valid directory.")
        return

    for file in folder.glob("*.mp4"):
        print(f"Processing {file.name}...")
        try:
            audio_info = get_audio_info(str(file))
            sample_rate = audio_info['sample_rate']
            channels = audio_info['channels']
            
            if sample_rate != 48000 or channels > 1:
                print(f"  Current audio: {sample_rate} Hz, {channels} channel(s)")
                print(f"  Converting to 48000 Hz mono...")
                temp_output = file.with_name(f"temp_{file.name}")
                convert_audio(str(file), str(temp_output))
                file.unlink()
                temp_output.rename(file)
                print(f"  Conversion complete.")
            else:
                print(f"  Audio is already 48000 Hz mono. No conversion needed.")
        except Exception as e:
            print(f"  Error processing {file.name}: {str(e)}")

def main():
    if len(sys.argv) > 1:
        folder_path = sys.argv[1]
    else:
        folder_path = input("Enter the folder path containing MP4 files: ")
    
    process_folder(folder_path)
    print("Processing complete.")

if __name__ == "__main__":
    main()