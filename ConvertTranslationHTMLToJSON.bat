import os
import json
from bs4 import BeautifulSoup
import re

def html_to_json(html_file):
    with open(html_file, 'r', encoding='utf-8') as file:
        soup = BeautifulSoup(file, 'html.parser')

    table = soup.find('table', class_='MsoNormalTable')
    rows = table.find_all('tr')[1:]  # Skip header row

    slides = []
    for row in rows:
        cells = row.find_all('td')
        if len(cells) == 3:
            name = cells[0].text.strip()
            english = cells[1].text.strip()
            translation = cells[2].text.strip()

            # Remove extra whitespace and newlines
            english = re.sub(r'\s+', ' ', english).strip()
            translation = re.sub(r'\s+', ' ', translation).strip()

            slides.append({
                "name": name,
                "english": english,
                "translation": translation
            })

    return {"slides": slides}

def main():
    input_directory = '.'  # Current directory
    output_directory = '.'  # Current directory

    for filename in os.listdir(input_directory):
        if filename.endswith('.htm') or filename.endswith('.html'):
            html_file = os.path.join(input_directory, filename)
            json_data = html_to_json(html_file)
            
            output_filename = os.path.splitext(filename)[0] + '.json'
            output_file = os.path.join(output_directory, output_filename)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            print(f"Converted {filename} to {output_filename}")

if __name__ == "__main__":
    main()