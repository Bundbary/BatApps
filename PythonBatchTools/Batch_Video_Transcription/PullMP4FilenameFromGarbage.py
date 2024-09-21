import re
import sys
import os
from bs4 import BeautifulSoup

def extract_mp4_filenames(html_content):
    # Use BeautifulSoup to parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Regular expression to match mp4 filenames
    pattern = r'[\w\-\.]+\.MP4'
    
    filenames = set()
    
    # Search in all tag contents
    for string in soup.stripped_strings:
        matches = re.findall(pattern, string, re.IGNORECASE)
        filenames.update(matches)
    
    # Search in all attribute values
    for tag in soup.find_all():
        for attr in tag.attrs.values():
            if isinstance(attr, str):
                matches = re.findall(pattern, attr, re.IGNORECASE)
                filenames.update(matches)
            elif isinstance(attr, list):
                for item in attr:
                    if isinstance(item, str):
                        matches = re.findall(pattern, item, re.IGNORECASE)
                        filenames.update(matches)
    
    # Sort the unique filenames
    return sorted(filenames)

def main():
    # Check if a file path is provided as an argument
    if len(sys.argv) != 2:
        print("Usage: python script.py <path_to_html_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Check if the file exists
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' does not exist.")
        sys.exit(1)
    
    # Read HTML content from the file
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except IOError as e:
        print(f"Error reading file: {e}")
        sys.exit(1)
    
    # Extract and sort mp4 filenames
    mp4_filenames = extract_mp4_filenames(html_content)
    
    # Print the sorted list of filenames
    for filename in mp4_filenames:
        print(filename)
    
    print(f"\nTotal MP4 files found: {len(mp4_filenames)}")

if __name__ == "__main__":
    main()