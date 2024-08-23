import csv
import os
import re

def sanitize_filename(filename):
    # Remove or replace characters that are problematic in filenames
    filename = re.sub(r'[^\w\-_\. ]', '_', filename)
    return filename.strip().replace(' ', '_')

def rename_videos(csv_file, video_folder):
    with open(csv_file, 'r', encoding='utf-8') as f:
        csv_reader = csv.DictReader(f)
        for row in csv_reader:
            recorded_name = row['Recorded Name']
            actual_name = row['Actual Name']
            
            print(f"Recorded Name: {recorded_name}")
            print(f"Actual Name1: {actual_name}")
            
            # Sanitize the actual name for use as a filename
            sanitized_name = sanitize_filename(actual_name)
            print(f"Actual Name2: {sanitized_name}")
            
            old_path = os.path.join(video_folder, recorded_name)
            new_name = f"{sanitized_name}.MP4"
            new_path = os.path.join(video_folder, new_name)
            
            # Handle duplicate filenames
            counter = 1
            while os.path.exists(new_path):
                new_name = f"{sanitized_name}_{counter}.MP4"
                new_path = os.path.join(video_folder, new_name)
                counter += 1
            
            # Rename the file
            if os.path.exists(old_path):
                try:
                    os.rename(old_path, new_path)
                    print(f"Renamed: {old_path} to {new_path}")
                except Exception as e:
                    print(f"Error renaming file {recorded_name}: {str(e)}")
            else:
                print(f"File not found: {recorded_name}, skipping...")
            
            print()  # Empty line for readability

if __name__ == "__main__":
    csv_file = r"c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\Video_Clip_Re-Name_080924_Narrated_Raw.csv"
    video_folder = r"c:\Users\bpenn\ExpectancyLearning\Reckitt\Video\080924_Narrated_Raw\optimized_videos"
    
    rename_videos(csv_file, video_folder)

    input("Press Enter to exit...")