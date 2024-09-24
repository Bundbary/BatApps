import os
import json
import subprocess
import logging
import requests
from pathlib import Path
from typing import Tuple, Union

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def search_directories(root_dir: str) -> list:
    """
    Recursively search directories for 'global_props.mp4' and 'global_props.json' files.
    """
    file_pairs = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if 'backup' in dirpath.lower():
            continue
        if 'global_props.mp4' in filenames and 'global_props.json' in filenames:
            file_pairs.append((
                os.path.join(dirpath, 'global_props.mp4'),
                os.path.join(dirpath, 'global_props.json')
            ))
    return file_pairs


def get_transcript_from_json(json_file: str) -> Union[str, None]:
    """
    Extract transcript from global_props.json file.
    """
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        transcript = data.get('transcript', [])
        
        if isinstance(transcript, list) and transcript:
            # Get the last item from the transcript list
            last_item = transcript[-1]
            if isinstance(last_item, dict) and 'text' in last_item:
                return last_item['text']
            else:
                logging.error(f"Unexpected format in the last transcript item: {last_item}")
                return None
        elif isinstance(transcript, dict) and 'text' in transcript:
            # Handle case where transcript is a single dictionary
            return transcript['text']
        else:
            logging.error(f"Unexpected transcript format in {json_file}")
            return None
    except Exception as e:
        logging.error(f"Error reading transcript from {json_file}: {e}")
        return None
    


def sanitize_text(text: Union[str, list]) -> str:
    """
    Sanitize text for API request.
    """
    if isinstance(text, list):
        # If text is a list, join its elements into a single string
        text = ' '.join(str(item) for item in text if item)
    elif not isinstance(text, str):
        logging.error(f"Expected string or list for sanitization, got {type(text)}")
        return ""
    # Remove non-printable characters and strip whitespace
    return ''.join(char for char in text if char.isprintable()).strip()


def generate_audio_from_transcript(transcript: str, api_key: str, output_file: str) -> bool:
    """
    Generate audio from transcript using Voicemaker API.
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    sanitized_text = sanitize_text(transcript)
    if not sanitized_text:
        logging.error("Sanitized text is empty.")
        return False

    logging.info(f"Text content (first 100 chars): {sanitized_text[:100]}...")

    max_chars = 1000  
    if len(sanitized_text) > max_chars:
        logging.warning(f"Text too long ({len(sanitized_text)} chars). Truncating to {max_chars} chars.")
        sanitized_text = sanitized_text[:max_chars]

    print (sanitized_text)


    payload = {
        "Engine": "neural",
        "VoiceId": "pro1-Thomas",
        "LanguageCode": "en-US",
        "Text": sanitized_text,
        "OutputFormat": "mp3",
        "SampleRate": "48000",
        "Effect": "default",
        "MasterVolume": "0",
        "MasterSpeed": "0",
        "MasterPitch": "0",
        "FileStore": "24"
    }

    try:
        response = requests.post("https://developer.voicemaker.in/voice/api", headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()

        if not result.get('success'):
            logging.error(f"API returned success=false. Message: {result.get('message')}")
            return False

        audio_url = result['path']
        print(f"\n\nAudio URL for manual testing: {audio_url}\n\n")  # Print URL for manual testing
        logging.info(f"Audio generated. URL for manual testing: {audio_url}")

        audio_response = requests.get(audio_url)
        audio_response.raise_for_status()

        with open(output_file, 'wb') as f:
            f.write(audio_response.content)

        return True

    except requests.RequestException as e:
        logging.error(f"Error in API request: {e}")
        return False
    

def get_duration(file_path: str) -> float:
    """
    Get the duration of a media file using FFprobe.
    """
    try:
        result = subprocess.run([
            'ffprobe', '-v', 'error', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', file_path
        ], capture_output=True, text=True, check=True)
        return float(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Error getting duration for {file_path}: {e}")
        return 0


def add_audio_to_video(video_file: str, audio_file: str, output_file: str) -> bool:
    """
    Add audio to video without re-encoding the video and without changing the video duration.
    """
    try:
        video_duration = get_duration(video_file)
        audio_duration = get_duration(audio_file)
        
        logging.info(f"Video duration: {video_duration}, Audio duration: {audio_duration}")
        
        ffmpeg_command = [
            'ffmpeg',
            '-i', video_file,
            '-i', audio_file,
            '-filter_complex', f'[1:a]apad=whole_dur={video_duration}[apadded];[apadded]atrim=0:{video_duration}[atrimmed]',
            '-map', '0:v',
            '-map', '[atrimmed]',
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            output_file
        ]
        
        logging.info(f"Executing FFmpeg command: {' '.join(ffmpeg_command)}")
        
        result = subprocess.run(ffmpeg_command, check=True, capture_output=True, text=True)
        logging.info(f"FFmpeg stdout: {result.stdout}")
        logging.info(f"FFmpeg stderr: {result.stderr}")
        
        return True
    except subprocess.CalledProcessError as e:
        logging.error(f"Error adding audio to video: {e}")
        logging.error(f"FFmpeg stderr: {e.stderr}")
        return False
    
   
def verify_output(input_video: str, input_audio: str, output_video: str) -> bool:
    """
    Verify that the output video meets the requirements.
    """
    input_video_duration = get_duration(input_video)
    input_audio_duration = get_duration(input_audio)
    output_video_duration = get_duration(output_video)
    
    logging.info(f"Input video duration: {input_video_duration}")
    logging.info(f"Input audio duration: {input_audio_duration}")
    logging.info(f"Output video duration: {output_video_duration}")
    
    if abs(input_video_duration - output_video_duration) > 0.1:  # Allow for small discrepancies
        logging.error(f"Output video duration ({output_video_duration}) does not match input video duration ({input_video_duration})")
        return False
    
    if input_audio_duration > input_video_duration:
        logging.warning(f"Audio duration ({input_audio_duration}) is longer than video duration ({input_video_duration}). Audio will be trimmed.")
    elif input_audio_duration < input_video_duration:
        logging.info(f"Audio duration ({input_audio_duration}) is shorter than video duration ({input_video_duration}). Audio will be padded.")
    
    return True



def process_video_pair(video_file: str, json_file: str, api_key: str) -> bool:
    """
    Process a pair of video and JSON files.
    """
    try:
        transcript = get_transcript_from_json(json_file)
        
        if transcript is None:
            logging.warning(f"No valid transcript found in {json_file}")
            return False
        
        temp_audio_file = f"{os.path.splitext(video_file)[0]}_temp_audio.mp3"
        temp_output_video = f"{os.path.splitext(video_file)[0]}_temp_output.mp4"
        
        if not generate_audio_from_transcript(transcript, api_key, temp_audio_file):
            return False
        
        if not add_audio_to_video(video_file, temp_audio_file, temp_output_video):
            return False
        
        if not verify_output(video_file, temp_audio_file, temp_output_video):
            return False
        
        # Replace the original file with the new one
        os.remove(video_file)
        os.rename(temp_output_video, video_file)
        logging.info(f"Replaced original file with new audio-added version: {video_file}")

        # Remove temporary audio file
        os.remove(temp_audio_file)
        logging.info(f"Removed temporary audio file: {temp_audio_file}")

        return True
    
    except Exception as e:
        logging.error(f"Error processing {video_file}: {e}")
        # Clean up any temporary files that might have been created
        if os.path.exists(temp_audio_file):
            os.remove(temp_audio_file)
        if os.path.exists(temp_output_video):
            os.remove(temp_output_video)
        return False
    

def main(root_dir: str, api_key: str):
    """
    Main function to process all video files in the directory structure.
    """
    file_pairs = search_directories(root_dir)
    
    for video_file, json_file in file_pairs:
        logging.info(f"Processing folder: {os.path.dirname(video_file)}")
        if process_video_pair(video_file, json_file, api_key):
            logging.info(f"Successfully processed {video_file}")
        else:
            logging.warning(f"Failed to process {video_file}")

if __name__ == "__main__":
    root_directory = input("Enter the root folder path: ")
    api_key = "9c73f0e0-6e14-11ef-9d35-2ff8558a697f"  # Replace with your actual API key
    main(root_directory, api_key)