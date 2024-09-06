import json
import re
import os

def clean_filename(name):
    # Replace periods with underscores and remove other punctuation
    name = re.sub(r'\.', '_', name)
    name = re.sub(r'[^\w\s-]', '', name)
    # Remove newline characters and extra spaces
    name = re.sub(r'\s+', ' ', name).strip()
    return name

def remove_newlines(text):
    # Remove '\n' characters
    return re.sub(r'\\n', '', text)

def create_text_files(json_file):
    # Get the directory of the JSON file
    json_dir = os.path.dirname(json_file)
    
    # Create 'output' directory in the same folder as the JSON file
    output_dir = os.path.join(json_dir, 'output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Read the JSON file
    with open(json_file, 'r', encoding='utf-8') as file:
        data = json.load(file)

    # Extract slides data
    slides = data['slides']

    # Process each slide
    for slide in slides:
        # Clean the filename
        filename = clean_filename(slide['name']) + '.txt'
        
        # Get the translation content and remove newlines
        content = remove_newlines(slide['translation'])

        # Write content to file in the output directory
        output_file = os.path.join(output_dir, filename)
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(content)

        print(f"Created file: {output_file}")

# Run the script
if __name__ == "__main__":
    # Use raw string for file path
    json_file_path = r'c:\Users\bpenn\ExpectancyLearning\BatApps\PythonBatchTools\PullJSONFromHTMLTable\slides.json'
    create_text_files(json_file_path)