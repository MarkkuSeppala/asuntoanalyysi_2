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
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def setup_driver(headless=False, download_dir=None):
    """Set up and return a configured Chrome WebDriver.
    
    Args:
        headless (bool): Whether to run in headless mode. Set to False if having trouble locating elements.
        download_dir (str): Directory where files will be downloaded.
    """
    chrome_options = Options()
    if headless:
        chrome_options.add_argument("--headless=new")  # Use newer headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")  # Set larger window size
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")  # Try to avoid detection
    chrome_options.add_argument(f"--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.9999.99 Safari/537.36")
    
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
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)
    
    # Initialize the Chrome WebDriver with the system's Chrome browser
    driver = webdriver.Chrome(options=chrome_options)
    
    # Execute CDP commands to avoid being detected as automation
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
    })
    
    return driver

def is_valid_pdf(pdf_path):
    """
    Check if a PDF file is valid by attempting to read it.
    
    Args:
        pdf_path (str): Path to the PDF file to validate
        
    Returns:
        bool: True if the PDF is valid, False otherwise
    """
    try:
        # Check if file exists and has size greater than 0
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) == 0:
            logger.warning(f"PDF file does not exist or has zero size: {pdf_path}")
            return False
            
        # Try to open and read the PDF
        with open(pdf_path, 'rb') as f:
            try:
                reader = PyPDF2.PdfReader(f)
                if len(reader.pages) == 0:
                    logger.warning("PDF has no pages")
                    return False
                
                # Try to read the first page to verify content
                _ = reader.pages[0].extract_text()
                return True
            except Exception as e:
                logger.warning(f"Error validating PDF: {e}")
                return False
    except Exception as e:
        logger.warning(f"Exception while validating PDF: {e}")
        return False

def scrape_property_html(url, driver=None):
    """
    Scrape the property details directly from the HTML as a fallback method.
    
    Args:
        url (str): The URL of the property listing
        driver (WebDriver, optional): An existing WebDriver instance
        
    Returns:
        str: Extracted property information as text
    """
    logger.info(f"Scraping property HTML from {url}")
    close_driver = False
    
    try:
        if driver is None:
            driver = setup_driver(headless=True)
            close_driver = True
            
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Get the page source
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract property details
        property_info = []
        
        # Try to get the title
        title_elem = soup.find('h1')
        if title_elem:
            property_info.append(f"Otsikko: {title_elem.text.strip()}")
        
        # Try to get the price
        price_elem = soup.select_one('[class*="price"]')
        if price_elem:
            property_info.append(f"Hinta: {price_elem.text.strip()}")
        
        # Try to get property details
        detail_elems = soup.select('[class*="detail"], [class*="info"], [class*="data"]')
        for elem in detail_elems:
            text = elem.text.strip()
            if text and len(text) < 200:  # Filter out long text blocks
                property_info.append(text)
        
        # Try to get the description
        desc_elem = soup.select_one('[class*="description"], [class*="desc"]')
        if desc_elem:
            property_info.append(f"Kuvaus: {desc_elem.text.strip()}")
        
        # Join all the info with line breaks
        result = "\n\n".join(property_info)
        logger.info(f"Successfully scraped HTML content ({len(result)} characters)")
        return result
        
    except Exception as e:
        logger.error(f"Error scraping HTML: {e}")
        return f"Error scraping property details: {str(e)}"
    
    finally:
        if close_driver and driver:
            driver.quit()

def download_pdf_with_retry(url, output_filename=None, headless=False, max_retries=3):
    """
    Download a PDF with retry mechanism.
    
    Args:
        url (str): The URL of the property listing.
        output_filename (str, optional): The filename to save the PDF as.
        headless (bool): Whether to run in headless mode.
        max_retries (int): Maximum number of retry attempts.
        
    Returns:
        str: The path to the downloaded PDF file or None if all attempts fail.
    """
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} to download PDF from {url}")
            
            # Use non-headless mode on retry attempts
            use_headless = headless if attempt == 0 else False
            
            # Add a delay between retries with increasing backoff
            if attempt > 0:
                delay = random.uniform(2, 5) * attempt
                logger.info(f"Waiting {delay:.1f} seconds before retry...")
                time.sleep(delay)
                
            # Attempt to download the PDF
            pdf_path = download_pdf(url, output_filename, headless=use_headless)
            
            # Validate the PDF
            if is_valid_pdf(pdf_path):
                logger.info(f"Successfully downloaded and validated PDF on attempt {attempt + 1}")
                return pdf_path
            else:
                logger.warning(f"Downloaded PDF failed validation on attempt {attempt + 1}")
                os.remove(pdf_path)  # Remove the invalid PDF
                raise Exception("Downloaded PDF failed validation")
                
        except Exception as e:
            last_exception = e
            logger.warning(f"Attempt {attempt + 1} failed: {e}")
    
    # If we got here, all attempts failed
    logger.error(f"All {max_retries} attempts to download PDF failed")
    if last_exception:
        logger.error(f"Last error: {last_exception}")
    
    return None

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
        property_id = url.split('/')[-1].split('?')[0]  # Remove query parameters
        output_filename = f"etuovi_{property_id}.pdf"
    
    # Create a temporary download directory
    temp_download_dir = os.path.join(os.getcwd(), f"temp_downloads_{int(time.time())}")
    os.makedirs(temp_download_dir, exist_ok=True)
    
    driver = setup_driver(headless=headless, download_dir=temp_download_dir)
    
    try:
        logger.info(f"Navigating to {url}")
        driver.get(url)
        
        # Wait for the page to load
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Give the page extra time to fully load
        time.sleep(3)
        
        # Scroll down to make the PDF button visible (multiple scrolls to ensure it's in view)
        logger.info("Scrolling to find the PDF button...")
        for _ in range(5):
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)
        
        # Find the "TULOSTA PDF" button using multiple strategies
        logger.info("Looking for the PDF button...")
        pdf_button = None
        
        # Try various strategies to find the button
        try:
            # Strategy 1: Find by scanning all buttons for PDF-related content
            all_buttons = driver.find_elements(By.TAG_NAME, 'button')
            for button in all_buttons:
                try:
                    button_html = button.get_attribute("innerHTML").lower()
                    if "tulosta" in button_html or "pdf" in button_html or "print" in button_html:
                        pdf_button = button
                        logger.info("Found PDF button by scanning all buttons")
                        break
                except:
                    continue
                    
            # Strategy 2: Look for links with PDF content
            if not pdf_button:
                all_links = driver.find_elements(By.TAG_NAME, 'a')
                for link in all_links:
                    try:
                        link_html = link.get_attribute("innerHTML").lower()
                        if "tulosta" in link_html or "pdf" in link_html or "print" in link_html:
                            pdf_button = link
                            logger.info("Found PDF link by scanning all links")
                            break
                    except:
                        continue
                        
            # Strategy 3: Try to find by XPath
            if not pdf_button:
                xpath_patterns = [
                    "//button[contains(., 'PDF')]",
                    "//a[contains(., 'PDF')]",
                    "//button[contains(., 'Tulosta')]",
                    "//a[contains(., 'Tulosta')]",
                    "//button[contains(., 'Print')]",
                    "//a[contains(., 'Print')]"
                ]
                
                for xpath in xpath_patterns:
                    try:
                        elements = driver.find_elements(By.XPATH, xpath)
                        if elements:
                            pdf_button = elements[0]
                            logger.info(f"Found PDF button using XPath: {xpath}")
                            break
                    except:
                        continue
                        
        except Exception as e:
            logger.warning(f"Error while searching for PDF button: {str(e)}")
        
        if not pdf_button:
            raise Exception("Could not find the PDF button")
        
        # Click the PDF button
        logger.info("Clicking the PDF button...")
        driver.execute_script("arguments[0].scrollIntoView(true);", pdf_button)
        time.sleep(2)
        
        # Try to click using multiple methods
        try:
            # Method 1: JavaScript click
            driver.execute_script("arguments[0].click();", pdf_button)
        except:
            try:
                # Method 2: Direct Selenium click
                pdf_button.click()
            except:
                # Method 3: Action chains
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(driver).move_to_element(pdf_button).click().perform()
        
        # Wait longer for the PDF to load/download
        logger.info("Waiting for PDF to load...")
        time.sleep(10)  # Increased wait time
        
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
        max_wait_time = 60  # Increased maximum wait time to 60 seconds
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
                
                return os.path.abspath(output_path)
            
            # If no file found yet, wait a bit and check again
            time.sleep(1)
        
        # If we reach here, no PDF file was found in the download directory
        # Try to download directly from the blob URL if available
        if "blob:" in current_url:
            logger.info(f"No downloaded file found. Attempting to download from blob URL: {current_url}")
            
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
                    if (Date.now() - start > 10000) { // Increased timeout
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
                logger.info(f"PDF saved as {output_path}")
                
                return os.path.abspath(output_path)
            else:
                raise Exception("Failed to extract PDF content from blob URL")
        else:
            # If it's a direct PDF URL, download it with requests
            logger.info(f"No downloaded file found. Downloading PDF from URL: {current_url}")
            response = requests.get(current_url, stream=True)
            output_path = os.path.join(os.getcwd(), output_filename)
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:
                        f.write(chunk)
            logger.info(f"PDF saved as {output_path}")
            
            return os.path.abspath(output_path)
    
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise
    
    finally:
        # Close the browser
        try:
            driver.quit()
        except:
            pass
        
        # Clean up the temporary download directory
        try:
            shutil.rmtree(temp_download_dir)
        except Exception as e:
            logger.warning(f"Warning: Could not remove temporary directory: {str(e)}")

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
        
        # Verify the PDF file exists and is not empty
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        if os.path.getsize(pdf_path) == 0:
            raise ValueError(f"PDF file is empty: {pdf_path}")
        
        # Open the PDF file
        with open(pdf_path, 'rb') as pdf_file:
            try:
                # Create a PDF reader object
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                
                # Check if the PDF has pages
                if len(pdf_reader.pages) == 0:
                    raise ValueError("PDF has no pages")
                
                # Open text file for writing
                with open(text_path, 'w', encoding='utf-8') as text_file:
                    # Extract text from each page and write to text file
                    for page_num in range(len(pdf_reader.pages)):
                        page = pdf_reader.pages[page_num]
                        text = page.extract_text()
                        text_file.write(f"--- Page {page_num + 1} ---\n")
                        text_file.write(text if text else "[No text extracted from this page]")
                        text_file.write('\n\n')
                
                logger.info(f"PDF successfully converted to text: {text_path}")
                return text_path
                
            except Exception as e:
                logger.error(f"Error reading PDF: {e}")
                # If PDF reading fails, try to scrape the original URL
                raise
                
    except Exception as e:
        logger.error(f"Error converting PDF to text: {str(e)}")
        raise

def get_property_info(url, output_filename=None, headless=False):
    """
    Get property information from Etuovi, first trying PDF download, then falling back to HTML scraping.
    
    Args:
        url (str): The URL of the property listing.
        output_filename (str, optional): The filename to save any downloaded files.
        headless (bool): Whether to run in headless mode.
        
    Returns:
        tuple: (text_content, source_type) where source_type is 'pdf' or 'html'
    """
    logger.info(f"Getting property info from {url}")
    
    # First try PDF download with retry mechanism
    try:
        pdf_path = download_pdf_with_retry(url, output_filename, headless=headless, max_retries=3)
        
        if pdf_path and os.path.exists(pdf_path) and is_valid_pdf(pdf_path):
            # Successfully downloaded and validated PDF
            text_path = convert_pdf_to_text(pdf_path)
            
            # Read the text file
            with open(text_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
                
            # Clean up temp files
            try:
                os.remove(text_path)
            except:
                pass
                
            return text_content, 'pdf'
    except Exception as e:
        logger.error(f"PDF download and conversion failed: {e}")
    
    # If PDF method failed, fall back to HTML scraping
    logger.info("Falling back to HTML scraping")
    text_content = scrape_property_html(url)
    return text_content, 'html'

def main():
    """Main function to parse arguments and download the PDF."""
    parser = argparse.ArgumentParser(description="Download PDF from Etuovi.com property listing and convert to text")
    parser.add_argument("url", help="URL of the property listing")
    parser.add_argument("output", nargs="?", help="Output filename (optional)")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode (hides browser UI)")
    parser.add_argument("--no-text", action="store_true", help="Skip converting PDF to text")
    args = parser.parse_args()
    
    try:
        # Default is now non-headless, but user can still request headless with flag
        headless = args.headless
        
        # Try with PDF method first
        pdf_path = download_pdf_with_retry(args.url, args.output, headless=headless)
        
        if pdf_path:
            logger.info(f"PDF downloaded successfully: {pdf_path}")
            
            # Convert PDF to text unless --no-text flag is used
            if not args.no_text:
                text_path = convert_pdf_to_text(pdf_path)
                logger.info(f"Text file created: {text_path}")
                
            return 0
        else:
            # Fall back to HTML scraping
            logger.info("PDF download failed, falling back to HTML scraping")
            text_content = scrape_property_html(args.url)
            
            # Save text content to file
            output_name = args.output or f"etuovi_{args.url.split('/')[-1].split('?')[0]}_html.txt"
            with open(output_name, 'w', encoding='utf-8') as f:
                f.write(text_content)
                
            logger.info(f"Property information saved to {output_name}")
            return 0
            
    except Exception as e:
        logger.error(f"Failed to get property information: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
