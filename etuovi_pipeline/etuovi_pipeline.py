#!/usr/bin/env python3
"""
Etuovi Pipeline

This script takes an Etuovi.com property listing URL, downloads the PDF,
and converts it to markdown format.

Usage:
    python etuovi_pipeline.py <url> [output_markdown_filename]

Example:
    python etuovi_pipeline.py https://www.etuovi.com/kohde/w67778 property_listing.md
"""

import os
import sys
import time
import argparse
import requests
import glob
import shutil
import re
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from docling.document_converter import DocumentConverter

def sanitize_filename(filename):
    """
    Remove invalid characters from a filename.
    
    Args:
        filename (str): The filename to sanitize.
    
    Returns:
        str: A sanitized filename safe for file system operations.
    """
    # Remove invalid filename characters
    sanitized = re.sub(r'[\\/*?:"<>|]', "", filename)
    return sanitized

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
        # Extract property ID from URL for default filename, removing any query parameters
        property_id = url.split('/')[-1].split('?')[0]
        property_id = sanitize_filename(property_id)
        output_filename = f"etuovi_{property_id}.pdf"
    else:
        # Ensure the provided filename is safe
        output_filename = sanitize_filename(output_filename)
    
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
                try:
                    shutil.copy2(downloaded_file, output_path)
                    print(f"PDF saved as {output_path}")
                except Exception as e:
                    print(f"Error copying file: {str(e)}")
                    # Try with a safe alternative approach
                    with open(downloaded_file, 'rb') as src_file:
                        with open(output_path, 'wb') as dst_file:
                            dst_file.write(src_file.read())
                    print(f"PDF saved as {output_path} using alternative method")
                
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

def convert_pdf_to_markdown(pdf_path, output_markdown=None):
    """
    Convert a PDF file to markdown format using docling.
    
    Args:
        pdf_path (str): Path to the PDF file.
        output_markdown (str, optional): Filename to save the markdown as.
            If not provided, a default name will be generated.
    
    Returns:
        str: The path to the markdown file.
    """
    print(f"Converting PDF to markdown: {pdf_path}")
    
    # Create default output filename if not provided
    if not output_markdown:
        output_markdown = os.path.splitext(os.path.basename(pdf_path))[0] + ".md"
    
    # Get absolute path for the output file
    output_path = os.path.join(os.getcwd(), output_markdown)
    
    # Convert the PDF to markdown using our improved dockling module
    from etuovi_pipeline.etuovi_dockling import convert_pdf_to_markdown as convert_pdf
    markdown_content = convert_pdf(pdf_path)
    
    if not markdown_content:
        raise Exception("Failed to convert PDF to markdown")
    
    # Save the markdown content to a file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)
    
    print(f"Markdown saved as {output_path}")
    return os.path.abspath(output_path)

def process_etuovi_listing(url, output_markdown=None, headless=True, cleanup=True):
    """
    Process an Etuovi listing: download PDF and convert to markdown.
    
    Args:
        url (str): URL of the Etuovi listing.
        output_markdown (str, optional): Output markdown filename.
        headless (bool): Whether to run browser in headless mode.
        cleanup (bool): Whether to clean up temporary files after processing.
    
    Returns:
        str: Absolute path to the output markdown file.
    """
    try:
        print(f"Processing Etuovi listing from URL: {url}")
        # Generate default output filename if not provided
        if not output_markdown:
            property_id = url.split('/')[-1].split('?')[0]
            property_id = sanitize_filename(property_id)
            output_markdown = f"etuovi_{property_id}.md"
        else:
            # Ensure the provided filename is safe
            output_markdown = sanitize_filename(output_markdown)
        
        # Download the PDF
        pdf_path = download_pdf(url, headless=headless)
        
        if not pdf_path or not os.path.exists(pdf_path):
            raise Exception(f"PDF download failed or file not found: {pdf_path}")
            
        # Convert the PDF to markdown
        markdown_path = convert_pdf_to_markdown(pdf_path, output_markdown)
        
        # Clean up the PDF file if requested
        if cleanup and pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"Removed temporary PDF file: {pdf_path}")
            except Exception as e:
                print(f"Warning: Could not remove temporary PDF file {pdf_path}: {e}")
        
        # Return the absolute path to the markdown file
        return os.path.abspath(markdown_path)
    except Exception as e:
        print(f"Error processing Etuovi listing: {e}")
        raise

def main():
    """Main function to parse arguments and process the Etuovi listing."""
    parser = argparse.ArgumentParser(description="Download Etuovi listing and convert to markdown")
    parser.add_argument("url", help="URL of the Etuovi property listing")
    parser.add_argument("output", nargs="?", help="Output markdown filename (optional)")
    parser.add_argument("--no-headless", action="store_true", help="Run in non-headless mode (shows browser UI)")
    args = parser.parse_args()
    
    try:
        markdown_path = process_etuovi_listing(args.url, args.output, headless=not args.no_headless)
        print(f"Process completed successfully. Markdown file: {markdown_path}")
    except Exception as e:
        print(f"Error processing Etuovi listing: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 