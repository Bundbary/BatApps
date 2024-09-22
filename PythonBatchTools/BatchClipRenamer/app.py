import os
import shutil
import re

def organize_project_files(main_folder):
    # Scan the main folder for project folders
    for project_folder in os.listdir(main_folder):
        project_path = os.path.join(main_folder, project_folder)
        
        if os.path.isdir(project_path):
            print(f"Processing project: {project_folder}")
            
            # Create a new subfolder with the same name as the project folder
            new_subfolder = os.path.join(project_path, project_folder)
            os.makedirs(new_subfolder, exist_ok=True)
            
            # Scan for subfolders matching the pattern
            for subfolder in os.listdir(project_path):
                subfolder_path = os.path.join(project_path, subfolder)
                if os.path.isdir(subfolder_path):
                    match = re.match(f"{project_folder}_(\d+)_D_clips", subfolder)
                    if match:
                        suffix = match.group(1)
                        print(f"  Processing subfolder: {subfolder}")
                        
                        # Process MP4 files in the subfolder
                        for filename in os.listdir(subfolder_path):
                            if filename.lower().endswith('.mp4'):
                                old_path = os.path.join(subfolder_path, filename)
                                new_filename = f"{suffix}_{filename}"
                                new_path = os.path.join(new_subfolder, new_filename)
                                
                                # Copy and rename the file
                                shutil.copy2(old_path, new_path)
                                print(f"    Copied and renamed: {filename} -> {new_filename}")

    print("File organization complete.")

# Usage
# main_folder = r"PATH_TO_YOUR_MAIN_FOLDER"
main_folder = input("Enter the path to the main folder: ")
organize_project_files(main_folder)