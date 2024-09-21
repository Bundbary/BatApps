import os
import zipfile
import shutil

def unzip_files_in_directory(directory):
    # Iterate through all files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.zip'):
            # Full path to the zip file
            zip_path = os.path.join(directory, filename)
            
            # Create a new folder name (without .zip extension)
            folder_name = os.path.splitext(filename)[0]
            folder_path = os.path.join(directory, folder_name)
            
            # Create the new folder
            os.makedirs(folder_path, exist_ok=True)
            
            # Unzip the file into the new folder
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(folder_path)
            
            print(f"Unzipped {filename} to {folder_path}")

# Get the directory path from the user
directory = input("Enter the folder path to search for zip files: ")

# Check if the directory exists
if os.path.exists(directory):
    unzip_files_in_directory(directory)
else:
    print("The specified directory does not exist.")