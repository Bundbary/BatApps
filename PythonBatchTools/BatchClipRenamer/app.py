import os
import re

def rename_files_in_folder(folder_path):
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            if file.endswith('.MP4'):
                # Extract the last 4 digits before the extension
                match = re.search(r'_(\d{4})_D\.MP4$', file)
                if match:
                    new_name = match.group(1) + '.MP4'
                    old_path = os.path.join(root, file)
                    new_path = os.path.join(root, new_name)
                    
                    try:
                        os.rename(old_path, new_path)
                        print(f"Renamed: {file} -> {new_name}")
                    except Exception as e:
                        print(f"Error renaming {file}: {e}")
                else:
                    print(f"Skipped: {file} (doesn't match expected format)")

def main():
    folder_path = input("Enter the path to the main folder: ")
    if os.path.isdir(folder_path):
        rename_files_in_folder(folder_path)
        print("File renaming complete.")
    else:
        print("Invalid folder path. Please enter a valid directory path.")

if __name__ == "__main__":
    main()