from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

import os

# SharePoint site and folder details
site_url = "https://sdiclarity.sharepoint.com/sites/ReckittEclipse-TrainingVideos"
# folder_url = "/sites/ReckittEclipse-TrainingVideos/Shared Documents/Training Videos/Training Video Footage/Jeremy Narrated Primary/August 9 Narrated/raw"

folder_url = "/sites/ReckittEclipse-TrainingVideos/Shared Documents/Training Videos/Training Video Footage/Secondary Packaging"







# Authentication details
username = "bpennington@sdiclarity.com"
# password = "(JJj-vXN3EHpPtv"
password = "Bund0064!"




# Directory to save downloaded files
download_dir = "D:/Brad/raw_video"  # Change to your desired path

# Ensure the download directory exists
os.makedirs(download_dir, exist_ok=True)

# Authenticate
ctx_auth = AuthenticationContext(site_url)
if ctx_auth.acquire_token_for_user(username, password):
    ctx = ClientContext(site_url, ctx_auth)
    web = ctx.web
    ctx.load(web)
    ctx.execute_query()

    # Get the folder
    folder = ctx.web.get_folder_by_server_relative_url(folder_url)
    files = folder.files
    ctx.load(files)
    ctx.execute_query()

    print(f"Found {len(files)} files in folder: {folder_url}")

    # Download each file
    for file in files:
        file_url = file.serverRelativeUrl
        file_name = file.name
        local_file_path = os.path.join(download_dir, file_name)

        # Check if the file is an MP4
        if not file_name.lower().endswith('.mp4'):
            print(f"Skipping non-MP4 file: {file_name}")
            continue

        # Check if the file already exists locally
        if os.path.exists(local_file_path):
            print(f"File already exists, skipping: {file_name}")
            continue

        print(f"Starting download of: {file_name}")
        try:
            with open(local_file_path, "wb") as local_file:
                file = File.open_binary(ctx, file_url)
                local_file.write(file.content)
            print(f"Completed download of: {file_name}")
        except Exception as e:
            print(f"Error downloading {file_name}: {str(e)}")
            print("Skipping to next file...")
else:
    print("Authentication failed")