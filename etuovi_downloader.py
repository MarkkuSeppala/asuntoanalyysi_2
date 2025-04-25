#!/usr/bin/env python3
"""
Etuovi PDF Downloader

This script downloads a PDF file from an Etuovi.com property listing.
It navigates to the given URL, finds the "TULOSTA PDF" button, clicks it,
and downloads the resulting PDF file. It then converts the PDF to text format.

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
import PyPDF2
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException, 
    NoSuchElementException, 
    ElementClickInterceptedException,
    StaleElementReferenceException,
    WebDriverException
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Maximum number of retry attempts
MAX_RETRIES = 3

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

def find_pdf_button(driver):
    """
    Find the PDF button using various strategies.
    
    Args:
        driver (WebDriver): Selenium WebDriver instance
        
    Returns:
        WebElement or None: The PDF button if found, None otherwise
    """
    logger.info("Looking for the PDF button...")
    pdf_button = None
    
    # Try multiple strategies to find the button
    strategies = [
        # Strategy 1: Scan all buttons for PDF-related content
        lambda: next((button for button in driver.find_elements(By.TAG_NAME, 'button') 
                     if any(text in button.get_attribute("innerHTML") 
                           for text in ["Tulosta", "PDF", "print"])), None),
        
        # Strategy 2: Look for specific CSS selectors that might contain the button
        lambda: driver.find_element(By.CSS_SELECTOR, 'button[data-test-id*="print"]'),
        
        # Strategy 3: Look for elements with specific class names
        lambda: driver.find_element(By.CSS_SELECTOR, '.print-button, .pdf-button, [class*="print"], [class*="pdf"]'),
        
        # Strategy 4: Look for specific text content
        lambda: driver.find_element(By.XPATH, '//button[contains(text(), "Tulosta") or contains(text(), "PDF")]')
    ]
    
    # Try each strategy until one works
    for i, strategy in enumerate(strategies):
        try:
            pdf_button = strategy()
            if pdf_button:
                logger.info(f"Found PDF button using strategy {i+1}")
                return pdf_button
        except Exception as e:
            logger.debug(f"Strategy {i+1} failed: {str(e)}")
    
    return None

def download_with_retry(url, output_filename=None, headless=False, max_retries=MAX_RETRIES):
    """
    Download a PDF from an Etuovi.com property listing with retry logic.
    
    Args:
        url (str): The URL of the property listing.
        output_filename (str, optional): The filename to save the PDF as.
        headless (bool): Whether to run in headless mode.
        max_retries (int): Maximum number of retry attempts.
    
    Returns:
        str: The path to the downloaded PDF file.
    
    Raises:
        Exception: If all download attempts fail.
    """
    if not output_filename:
        # Extract property ID from URL for default filename
        property_id = url.split('/')[-1]
        output_filename = f"etuovi_{property_id}.pdf"
    
    attempts = 0
    last_exception = None
    
    while attempts < max_retries:
        try:
            if attempts > 0:
                # Calculate backoff time with jitter for retries
                backoff_time = min(2 ** attempts + random.uniform(0, 1), 10)
                logger.info(f"Retry attempt {attempts}/{max_retries-1}. Waiting {backoff_time:.2f} seconds...")
                time.sleep(backoff_time)
                
            # Log the attempt
            logger.info(f"Download attempt {attempts+1}/{max_retries}")
            
            # Try to download the PDF
            result = download_pdf_single_attempt(url, output_filename, headless)
            
            # If we got here, the download was successful
            logger.info(f"Successfully downloaded PDF on attempt {attempts+1}")
            return result
            
        except Exception as e:
            last_exception = e
            attempts += 1
            logger.error(f"Attempt {attempts} failed: {str(e)}")
    
    # If we've exhausted all retries, raise the last exception
    logger.error(f"All {max_retries} download attempts failed")
    raise last_exception or Exception("Failed to download PDF after multiple attempts")

def download_pdf_single_attempt(url, output_filename, headless=False):
    """
    Perform a single attempt to download a PDF from an Etuovi.com property listing.
    
    Args:
        url (str): The URL of the property listing.
        output_filename (str): The filename to save the PDF as.
        headless (bool): Whether to run in headless mode.
    
    Returns:
        str: The path to the downloaded PDF file.
        
    Raises:
        Exception: If the download fails.
    """
    # Create a temporary download directory
    temp_download_dir = os.path.join(os.getcwd(), f"temp_downloads_{int(time.time())}")
    os.makedirs(temp_download_dir, exist_ok=True)
    
    driver = None
    
    try:
        logger.info(f"Navigating to {url}")
        driver = setup_driver(headless=headless, download_dir=temp_download_dir)
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Scroll down to make the PDF button visible (multiple scrolls to ensure it's in view)
        logger.info("Scrolling to find the PDF button...")
        for _ in range(5):  # Increased scrolls from 3 to 5 for better coverage
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(0.5)
        
        # Find the PDF button
        pdf_button = find_pdf_button(driver)
        
        if not pdf_button:
            raise Exception("Could not find the PDF button after trying multiple strategies")
        
        # Click the PDF button
        logger.info("Clicking the PDF button...")
        driver.execute_script("arguments[0].scrollIntoView(true);", pdf_button)
        time.sleep(1)
        
        # Try direct click first, then JavaScript click as fallback
        try:
            pdf_button.click()
        except (ElementClickInterceptedException, StaleElementReferenceException):
            logger.info("Direct click failed, trying JavaScript click...")
            driver.execute_script("arguments[0].click();", pdf_button)
        
        # Wait for the PDF to load in a new tab or iframe
        time.sleep(5)  # Allow time for the PDF to load
        
        # Check if a new tab was opened
        if len(driver.window_handles) > 1:
            # Switch to the new tab
            driver.switch_to.window(driver.window_handles[1])
            logger.info("Switched to new tab")
        
        # Get the current URL (which might be the PDF URL)
        current_url = driver.current_url
        logger.info(f"Current URL after clicking: {current_url}")
        
        # Wait for the download to complete
        logger.info("Waiting for download to complete...")
        max_wait_time = 40  # Increased maximum wait time from 30 to 40 seconds
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check if any PDF files have been downloaded
            pdf_files = glob.glob(os.path.join(temp_download_dir, "*.pdf"))
            if pdf_files:
                # Found a downloaded PDF file
                downloaded_file = pdf_files[0]  # Take the first PDF file found
                logger.info(f"Found downloaded file: {downloaded_file}")
                
                # Copy the file to the desired output location
                output_path = os.path.join(os.getcwd(), output_filename)
                shutil.copy2(downloaded_file, output_path)
                logger.info(f"PDF saved as {output_path}")
                
                # Verify the PDF file size
                if os.path.getsize(output_path) < 1000:  # Less than 1KB is suspicious
                    raise Exception("Downloaded PDF file is too small, may be corrupt")
                
                return os.path.abspath(output_path)
            
            # If no file found yet, wait a bit and check again
            time.sleep(1)
        
        # If we reach here, no PDF file was found in the download directory
        logger.warning("No PDF file found in download directory within the time limit")
        
        # Try to download directly from the blob URL if available
        if "blob:" in current_url:
            logger.info(f"Attempting to download from blob URL: {current_url}")
            
            try:
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
                    logger.info(f"PDF saved from blob URL as {output_path}")
                    
                    # Verify the PDF file size
                    if os.path.getsize(output_path) < 1000:  # Less than 1KB is suspicious
                        raise Exception("Downloaded PDF file from blob URL is too small, may be corrupt")
                    
                    return os.path.abspath(output_path)
                else:
                    raise Exception("Failed to extract PDF content from blob URL")
            except Exception as blob_error:
                logger.error(f"Blob URL extraction failed: {str(blob_error)}")
                raise Exception(f"Blob URL extraction failed: {str(blob_error)}")
        else:
            # If it's a direct PDF URL, download it with requests
            try:
                logger.info(f"Downloading PDF from direct URL: {current_url}")
                response = requests.get(current_url, stream=True, timeout=30)
                
                if response.status_code != 200:
                    raise Exception(f"HTTP error: {response.status_code}")
                
                if 'application/pdf' not in response.headers.get('content-type', '').lower():
                    raise Exception("The downloaded content is not a PDF")
                
                output_path = os.path.join(os.getcwd(), output_filename)
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=1024):
                        if chunk:
                            f.write(chunk)
                logger.info(f"PDF saved from direct URL as {output_path}")
                
                # Verify the PDF file size
                if os.path.getsize(output_path) < 1000:  # Less than 1KB is suspicious
                    raise Exception("Downloaded PDF file from direct URL is too small, may be corrupt")
                
                return os.path.abspath(output_path)
            except Exception as request_error:
                logger.error(f"Direct URL download failed: {str(request_error)}")
                raise Exception(f"Direct URL download failed: {str(request_error)}")
    
    except Exception as e:
        logger.error(f"Error in download attempt: {str(e)}")
        raise
    
    finally:
        # Close the browser
        if driver:
            try:
                driver.quit()
            except Exception as e:
                logger.warning(f"Error closing browser: {str(e)}")
        
        # Clean up the temporary download directory
        try:
            shutil.rmtree(temp_download_dir)
        except Exception as e:
            logger.warning(f"Could not remove temporary directory: {str(e)}")

def convert_pdf_to_text(pdf_path):
    """
    Convert a PDF file to text format.
    
    Args:
        pdf_path (str): Path to the PDF file.
    
    Returns:
        str: Path to the created text file.
    """
    try:
        logger.info(f"Converting PDF to text: {pdf_path}")
        # Create output text file path by changing extension
        text_path = os.path.splitext(pdf_path)[0] + '.txt'
        
        # Open the PDF file
        with open(pdf_path, 'rb') as pdf_file:
            # Create a PDF reader object
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            # Verify that the PDF has content
            if len(pdf_reader.pages) == 0:
                raise Exception("PDF file has no pages")
            
            # Open text file for writing
            with open(text_path, 'w', encoding='utf-8') as text_file:
                # Extract text from each page and write to text file
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    text_file.write(f"--- Page {page_num + 1} ---\n")
                    text_file.write(text)
                    text_file.write('\n\n')
        
        logger.info(f"PDF successfully converted to text: {text_path}")
        return text_path
    
    except Exception as e:
        logger.error(f"Error converting PDF to text: {str(e)}")
        raise

def main():
    """Main function to parse arguments and download the PDF."""
    parser = argparse.ArgumentParser(description="Download PDF from Etuovi.com property listing and convert to text")
    parser.add_argument("url", help="URL of the property listing")
    parser.add_argument("output", nargs="?", help="Output filename (optional)")
    parser.add_argument("--no-headless", action="store_true", help="Run in non-headless mode (shows browser UI)")
    parser.add_argument("--no-text", action="store_true", help="Skip converting PDF to text")
    parser.add_argument("--retries", type=int, default=MAX_RETRIES, help=f"Maximum number of retry attempts (default: {MAX_RETRIES})")
    args = parser.parse_args()
    
    try:
        # Use the retry wrapper function instead of direct download
        pdf_path = download_with_retry(
            args.url, 
            args.output, 
            headless=not args.no_headless,
            max_retries=args.retries
        )
        logger.info(f"PDF downloaded successfully: {pdf_path}")
        
        # Convert PDF to text unless --no-text flag is used
        if not args.no_text:
            text_path = convert_pdf_to_text(pdf_path)
            logger.info(f"Text file created: {text_path}")
        
        return 0
    except Exception as e:
        logger.error(f"Failed to download PDF or convert to text: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
