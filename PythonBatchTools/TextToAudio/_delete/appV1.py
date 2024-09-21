import os
import requests
from pathlib import Path
import openai

# Set your OpenAI API key
openai.api_key = 'sk--g2hiAUedCQ72Qk3DiAxxvKxkOEltseJThkuGGWCnCT3BlbkFJEoOjLUoOD1CCWxNlRMxF3-81c4FruygP7WruHdBocA'

def text_to_speech(text, output_file):
    response = openai.audio.speech.create(
        model="tts-1",
        # voice="alloy",
        # voice="echo",
        # voice="fable",
        # voice="nova",
        # onyx is a deeper male voice. The rest are fairly similar to each other.
        voice="onyx",
        # voice="shimmer",
        input=text
    )
    
    # Use the recommended streaming method
    with open(output_file, 'wb') as file:
        for chunk in response.iter_bytes():
            file.write(chunk)

def process_folder(folder_path):
    folder = Path(folder_path)
    
    for text_file in folder.glob('*.txt'):
        with open(text_file, 'r', encoding='utf-8') as file:
            text_content = file.read()
        
        output_file = text_file.with_suffix('.mp3')
        
        try:
            text_to_speech(text_content, str(output_file))
            print(f"Converted {text_file.name} to {output_file.name}")
        except Exception as e:
            print(f"Error processing {text_file.name}: {str(e)}")

if __name__ == "__main__":
    folder_path = input("Enter the path to the folder containing text files: ")
    process_folder(folder_path)