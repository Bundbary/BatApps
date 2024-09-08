import os
from pathlib import Path
import requests
import json
import re

def sanitize_text(text):
    text = ''.join(char for char in text if char.isprintable())
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def process_files(folder_path, api_key):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    for root, dirs, files in os.walk(folder_path):
        dirs[:] = [d for d in dirs if 'backup' not in d.lower()]

        for file in files:
            if file.endswith('_transcript.txt'):
                file_path = Path(root) / file
                output_file = file_path.with_suffix('.mp3')

                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        text = f.read()

                    sanitized_text = sanitize_text(text)
                    print(f"Processing file: {file_path}")
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
                            with open(output_file, 'wb') as f:
                                f.write(audio_response.content)
                            print(f"Generated MP3 for {file_path}")
                        else:
                            print(f"API returned success=false. Message: {result.get('message')}")
                            if "character limit" in result.get('message', '').lower():
                                print("You have reached your character limit. Please recharge your account at Voicemaker.")
                                break  # Stop processing further files
                    else:
                        print(f"API request failed with status code: {response.status_code}")
                        print(f"Response content: {response.text}")
                        if response.status_code == 400 and "character limit" in response.text.lower():
                            print("You have reached your character limit. Please recharge your account at Voicemaker.")
                            break  # Stop processing further files

                except Exception as e:
                    print(f"Error processing {file_path}: {str(e)}")

if __name__ == "__main__":
    folder_path = input("Enter the folder path: ")
    api_key = "9c73f0e0-6e14-11ef-9d35-2ff8558a697f"
    process_files(folder_path, api_key)