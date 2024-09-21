from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import os

# SharePoint site details
site_url = "https://sdiclarity.sharepoint.com/sites/ReckittEclipse-TrainingVideos/Shared%20Documents/Forms/AllItems.aspx?id=%2Fsites%2FReckittEclipse%2DTrainingVideos%2FShared%20Documents%2FTraining%20Videos%2FTraining%20Video%20Footage%2FSecondary%20Packaging"
download_dir = r"C:\Users\bpenn\Downloads"  # Change this to your preferred download directory

# Set up Chrome options
chrome_options = Options()
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": True
})

# Initialize the WebDriver
service = Service()  # You can specify the path to chromedriver here if it's not in PATH
driver = webdriver.Chrome(service=service, options=chrome_options)

# Navigate to the SharePoint site
driver.get(site_url)

def wait_and_find_element(by, value, timeout=20):
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )
        return element
    except TimeoutException:
        print(f"Timeout waiting for element: {value}")
        return None

# Function to log in (you may need to adjust this based on your login page structure)
def login():
    try:
        # Wait for the username field and enter username
        username_field = wait_and_find_element(By.NAME, "loginfmt")
        if username_field:
            username_field.send_keys("bpennington@sdiclarity.com")
            next_button = wait_and_find_element(By.ID, "idSIButton9")
            if next_button:
                next_button.click()
        
        # Wait for password field and enter password
        password_field = wait_and_find_element(By.NAME, "passwd")
        if password_field:
            password_field.send_keys("your_password_here")
            sign_in_button = wait_and_find_element(By.ID, "idSIButton9")
            if sign_in_button:
                sign_in_button.click()
        
        # Wait for and click "Stay signed in" if it appears
        stay_signed_in = wait_and_find_element(By.ID, "idSIButton9")
        if stay_signed_in:
            stay_signed_in.click()
    
    except Exception as e:
        print(f"An error occurred during login: {str(e)}")

# Log in
login()

# Wait for the file list to load
file_list = wait_and_find_element(By.CSS_SELECTOR, "[data-automationid='DetailsRow']")

if file_list:
    # Find all MP4 files
    mp4_files = driver.find_elements(By.XPATH, "//div[contains(@class, 'DetailsRow') and contains(., '.mp4')]")

    # Download each MP4 file
    for file in mp4_files:
        try:
            # Click on the file to open the context menu
            file.click()
            time.sleep(2)
            
            # Find and click the download button
            download_button = wait_and_find_element(By.XPATH, "//button[@name='Download']")
            if download_button:
                download_button.click()
            
            print(f"Downloading: {file.text}")
            
            # Wait for the download to complete (you may need to adjust the wait time)
            time.sleep(10)
        except Exception as e:
            print(f"An error occurred while downloading {file.text}: {str(e)}")

    print("Download process completed.")
else:
    print("Failed to load the file list. Please check your permissions and the SharePoint site structure.")

# Close the browser
driver.quit()