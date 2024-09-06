from bs4 import BeautifulSoup
import json


import sys
import os
import tkinter as tk
from tkinter import filedialog

# Prompt the user to select an HTML file
root = tk.Tk()
root.withdraw()

file_path = filedialog.askopenfilename(
    title="Select HTML file",
    filetypes=[("HTML files", "*.html"), ("All files", "*.*")]
)

if file_path:
    with open(file_path, "r") as file:
        html_content = file.read()
else:
    print("No file selected. Exiting.")
    sys.exit()
from bs4 import BeautifulSoup
import json
import re
import os

# Sample HTML content
html_content = """
<table>
    <tr>
        <th>Name</th>
        <th>English</th>
        <th>Translation</th>
    </tr>
    <tr>
        <td>00</td>
        <td>Welcome to Conveyor System Essentials!</td>
        <td>コンベヤシステムの基礎コースへようこそ！</td>
    </tr>
    <tr>
        <td>1.1</td>
        <td>fooooooooooo</td>
        <td>translated fooo</td>
    </tr>
</table>
"""

# Parse the HTML content
soup = BeautifulSoup(html_content, 'html.parser')

# Extract data from the table
slides = []
table = soup.find('table')
for row in table.find_all('tr')[1:]:  # Skip the header row
    cells = row.find_all('td')
    slide = {
        "name": cells[0].text,
        "english": cells[1].text,
        "translation": cells[2].text
    }
    slides.append(slide)

# Create the JSON structure
json_data = {
    "slides": slides
}

# Convert to JSON string
json_string = json.dumps(json_data, ensure_ascii=False, indent=4)

# Save JSON string to a file
json_filename = 'slides.json'
with open(json_filename, 'w', encoding='utf-8') as json_file:
    json_file.write(json_string)

# Function to create text files for each slide
def create_text_files(slides):
    for slide in slides:
        # Create a valid filename from the 'name' property
        filename = re.sub(r'[^\w\s]', '', slide['name']).replace('.', '_') + '.txt'
        
        # Write the 'translation' content to the text file
        with open(filename, 'w', encoding='utf-8') as text_file:
            text_file.write(slide['translation'])

# Create text files
create_text_files(slides)