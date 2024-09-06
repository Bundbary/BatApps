import json
import re
import os
import requests
from pathlib import Path

def clean_filename(name):
    name = re.sub(r'\.', '_', name)
    name = re.sub(r'[^\w\s-]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def remove_newlines(text):
    return re.sub(r'\\n', '', text)

def load_config():
    with open('config.json', 'r') as config_file:
        return json.load(config_file)

def text_to_speech_voicemaker(text, output_file, config):
    payload = config['payload'].copy()
    payload['Text'] = text

    response = requests.post(config['url'], headers=config['headers'], json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if result['success']:
            audio_url = result['path']
            audio_response = requests.get(audio_url)
            with open(output_file, 'wb') as file:
                file.write(audio_response.content)
            print(f"Created file: {output_file}")
        else:
            print(f"Error: {result['message']}")
    else:
        print(f"Error: API request failed with status code {response.status_code}")

def text_to_speech_other_api(text, output_file, config):
    payload = config['payload'].copy()
    payload['text'] = text

    response = requests.post(config['url'], headers=config['headers'], json=payload)
    
    if response.status_code == 200:
        with open(output_file, 'wb') as file:
            file.write(response.content)
        print(f"Created file: {output_file}")
    else:
        print(f"Error: API request failed with status code {response.status_code}")

def create_text_files(json_file, api_choice):
    config = load_config()
    
    if api_choice not in config:
        print(f"Error: API '{api_choice}' not found in configuration.")
        return

    api_config = config[api_choice]
    
    json_dir = Path(json_file).parent
    output_dir = json_dir / 'output'
    output_dir.mkdir(exist_ok=True)

    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    slides = data['slides']

    for slide in slides:
        filename = clean_filename(slide['name']) + '.mp3'
        content = remove_newlines(slide['translation'])
        output_file = output_dir / filename

        if api_choice == 'voicemaker':
            text_to_speech_voicemaker(content, str(output_file), api_config)
        elif api_choice == 'other_api':
            text_to_speech_other_api(content, str(output_file), api_config)
        else:
            print(f"Error: Unsupported API '{api_choice}'")

if __name__ == "__main__":
    json_file_path = r'c:\Users\bpenn\ExpectancyLearning\BatApps\PythonBatchTools\PullJSONFromHTMLTable\slides.json'
    api_choice = input("Choose an API (voicemaker/other_api): ").lower()
    create_text_files(json_file_path, api_choice)