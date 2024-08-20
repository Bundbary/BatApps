from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File

import os
import logging
import time
import requests

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SharePoint site and folder details
site_url = "https://sdiclarity.sharepoint.com/sites/ReckittEclipse-TrainingVideos"
folder_url = "/sites/ReckittEclipse-TrainingVideos/Shared Documents/Training Videos/Training Video Footage/Jeremy Narrated Primary/August 9 Narrated/raw"

# Authentication details
username = "bpennington@sdiclarity.com"
password = "(JJj-vXN3EHpPtv"

# Directory to save downloaded files
download_dir = "c:/Users/bpenn/ExpectancyLearning/BatApps/PythonBatchTools/output"

# Ensure the download directory exists
os.makedirs(download_dir, exist_ok=True)

def download_file_with_retry(ctx, file_url, local_file_path, max_retries=5, delay=5):
    for attempt in range(max_retries):
        try:
            with open(local_file_path, "wb") as local_file:
                file = File.open_binary(ctx, file_url)
                local_file.write(file.content)
            logger.info(f"Completed download of: {os.path.basename(local_file_path)}")
            return True
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 503:
                logger.warning(f"Service Unavailable (503) error. Attempt {attempt + 1} of {max_retries}. Retrying in {delay} seconds...")
                time.sleep(delay)
            else:
                logger.error(f"HTTP error occurred: {e}")
                return False
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            return False
    
    logger.error(f"Failed to download {os.path.basename(local_file_path)} after {max_retries} attempts")
    return False

# Authenticate
ctx_auth = AuthenticationContext(site_url)
if ctx_auth.acquire_token_for_user(username, password):
    ctx = ClientContext(site_url, ctx_auth)
    web = ctx.web
    ctx.load(web)
    ctx.execute_query()
    logger.info(f"Authentication successful. Web title: {web.properties['Title']}")

    try:
        # Get the folder
        folder = ctx.web.get_folder_by_server_relative_url(folder_url)
        files = folder.files
        ctx.load(files)
        ctx.execute_query()

        logger.info(f"Found {len(files)} files in folder: {folder_url}")

        # Download each MP4 file
        for file in files:
            file_url = file.serverRelativeUrl
            file_name = file.name

            # Skip non-MP4 files
            if not file_name.lower().endswith('.mp4'):
                logger.debug(f"Skipping non-MP4 file: {file_name}")
                continue

            local_file_path = os.path.join(download_dir, file_name)

            # Skip existing files
            if os.path.exists(local_file_path) and os.path.getsize(local_file_path) > 0:
                logger.debug(f"Skipping existing file: {file_name}")
                continue

            logger.info(f"Starting download of: {file_name}")
            success = download_file_with_retry(ctx, file_url, local_file_path)
            if not success:
                logger.error(f"Failed to download: {file_name}")

    except Exception as e:
        logger.error(f"Error accessing folder: {str(e)}", exc_info=True)
else:
    logger.error("Authentication failed")