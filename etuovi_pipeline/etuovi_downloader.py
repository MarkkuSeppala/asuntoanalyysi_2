#!/usr/bin/env python3
"""
Etuovi PDF Downloader

This script downloads a PDF file from an Etuovi.com property listing.
It navigates to the given URL, finds the "TULOSTA PDF" button, clicks it,
and downloads the resulting PDF file.

Usage:
    python etuovi_pdf_downloader.py <url> [output_filename]

Example:
    python etuovi_pdf_downloader.py https://www.etuovi.com/kohde/w67778 property_listing.pdf
"""

import os
import sys
import time
import argparse
import requests
import glob
import shutil
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver(headless=True, download_dir=None):
    """Set up and return a configured Chrome WebDriver.
    
    Args:
        headless (bool): Whether to run in headless mode. Set to False if having trouble locating elements.
        download_dir (str): Directory where files will be downloaded.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Set larger window size
    
    # Set PDF download preferences
    if not download_dir:
        download_dir = os.getcwd()
        
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "plugins.always_open_pdf_externally": True,
        "download.directory_upgrade": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Initialize the Chrome WebDriver with the system's Chrome browser
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def download_pdf(url, output_filename=None, headless=False):
    """
    Download a PDF from an Etuovi.com property listing.
    
    Args:
        url (str): The URL of the property listing.
        output_filename (str, optional): The filename to save the PDF as.
            If not provided, a default name will be generated.
        headless (bool): Whether to run in headless mode. Set to False if having trouble locating elements.
    
    Returns:
        str: The path to the downloaded PDF file.
    """
    if not output_filename:
        # Extract property ID from URL for default filename
        property_id = url.split('/')[-1]
        output_filename = f"etuovi_{property_id}.pdf"
    
    # Create a temporary download directory
    temp_download_dir = os.path.join(os.getcwd(), "temp_downloads")
    os.makedirs(temp_download_dir, exist_ok=True)
    
    # Clear any existing files in the temp directory
    for file in glob.glob(os.path.join(temp_download_dir, "*.pdf")):
        os.remove(file)
    
    driver = setup_driver(headless=headless, download_dir=temp_download_dir)
    
    try:
        print(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Scroll down to make the PDF button visible (multiple scrolls to ensure it's in view)
        print("Scrolling to find the PDF button...")
        for _ in range(3):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)
        
        # Find the "TULOSTA PDF" button using Strategy #5 (most effective based on user feedback)
        print("Looking for the PDF button...")
        pdf_button = None
        
        # Strategy 5: Find by scanning all buttons for PDF-related content
        try:
            all_buttons = driver.find_elements(By.TAG_NAME, 'button')
            for button in all_buttons:
                try:
                    if "Tulosta" in button.get_attribute("innerHTML") or "PDF" in button.get_attribute("innerHTML") or "print" in button.get_attribute("innerHTML").lower():
                        pdf_button = button
                        print("Found PDF button by scanning all buttons")
                        break
                except:
                    continue
        except Exception as e:
            print(f"Could not find button by scanning all buttons: {str(e)}")
        
        if not pdf_button:
            raise Exception("Could not find the PDF button")
        
        # Click the PDF button
        print("Clicking the PDF button...")
        driver.execute_script("arguments[0].scrollIntoView(true);", pdf_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", pdf_button)
        
        # Wait for the PDF to load in a new tab or iframe
        time.sleep(5)  # Allow time for the PDF to load
        
        # Check if a new tab was opened
        if len(driver.window_handles) > 1:
            # Switch to the new tab
            driver.switch_to.window(driver.window_handles[1])
            print("Switched to new tab")
        
        # Get the current URL (which might be the PDF URL)
        current_url = driver.current_url
        print(f"Current URL after clicking: {current_url}")
        
        # Wait for the download to complete
        print("Waiting for download to complete...")
        max_wait_time = 30  # Maximum wait time in seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check if any PDF files have been downloaded
            pdf_files = glob.glob(os.path.join(temp_download_dir, "*.pdf"))
            if pdf_files:
                # Found a downloaded PDF file
                downloaded_file = pdf_files[0]  # Take the first PDF file found
                print(f"Found downloaded file: {downloaded_file}")
                
                # Copy the file to the desired output location
                output_path = os.path.join(os.getcwd(), output_filename)
                shutil.copy2(downloaded_file, output_path)
                print(f"PDF saved as {output_path}")
                
                return os.path.abspath(output_path)
            
            # If no file found yet, wait a bit and check again
            time.sleep(1)
        
        # If we reach here, no PDF file was found in the download directory
        # Try to download directly from the blob URL if available
        if "blob:" in current_url:
            print(f"No downloaded file found. Attempting to download from blob URL: {current_url}")
            
            # Use JavaScript to get the PDF data
            pdf_content = driver.execute_script("""
                var xhr = new XMLHttpRequest();
                var blobUrl = arguments[0];
                xhr.open('GET', blobUrl, false);
                xhr.responseType = 'blob';
                xhr.send(null);
                
                var reader = new FileReader();
                reader.readAsDataURL(xhr.response);
                
                // This is a synchronous operation in this context
                var base64data = null;
                reader.onloadend = function() {
                    base64data = reader.result;
                }
                
                // Wait for reader to complete
                var start = Date.now();
                while (base64data === null) {
                    if (Date.now() - start > 5000) {
                        throw new Error('Timeout waiting for FileReader');
                    }
                }
                
                return base64data;
            """, current_url)
            
            # Extract the base64 data
            if pdf_content and "base64," in pdf_content:
                base64_data = pdf_content.split("base64,")[1]
                
                # Save the PDF file
                output_path = os.path.join(os.getcwd(), output_filename)
                with open(output_path, "wb") as f:
                    import base64
                    f.write(base64.b64decode(base64_data))
                print(f"PDF saved as {output_path}")
                
                return os.path.abspath(output_path)
            else:
                raise Exception("Failed to extract PDF content from blob URL")
        else:
            # If it's a direct PDF URL, download it with requests
            print(f"No downloaded file found. Downloading PDF from URL: {current_url}")
            response = requests.get(current_url, stream=True)
            output_path = os.path.join(os.getcwd(), output_filename)
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            print(f"PDF saved as {output_path}")
            
            return os.path.abspath(output_path)
    
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    
    finally:
        # Close the browser
        driver.quit()
        
        # Clean up the temporary download directory
        try:
            shutil.rmtree(temp_download_dir)
        except Exception as e:
            print(f"Warning: Could not remove temporary directory: {str(e)}")

def main():
    """Main function to parse arguments and download the PDF."""
    parser = argparse.ArgumentParser(description="Download PDF from Etuovi.com property listing")
    parser.add_argument("url", help="URL of the property listing")
    parser.add_argument("output", nargs="?", help="Output filename (optional)")
    parser.add_argument("--no-headless", action="store_true", help="Run in non-headless mode (shows browser UI)")
    args = parser.parse_args()
    
    try:
        pdf_path = download_pdf(args.url, args.output, headless=not args.no_headless)
        print(f"PDF downloaded successfully: {pdf_path}")
        return 0
    except Exception as e:
        print(f"Failed to download PDF: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
