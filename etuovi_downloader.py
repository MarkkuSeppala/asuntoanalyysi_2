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
import logging
import traceback
import uuid
import tempfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("logs/etuovi_downloader.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_driver(headless=True, download_dir=None):
    """Set up and return a configured Chrome WebDriver.
    
    Args:
        headless (bool): Whether to run in headless mode. Set to False if having trouble locating elements.
        download_dir (str): Directory where files will be downloaded.
    """
    try:
        logger.info("Alustetaan Chrome WebDriver...")
        chrome_options = Options()
        
        # Docker-ympäristöön tarvittavat asetukset
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-infobars')
        chrome_options.add_argument('--disable-notifications')
        chrome_options.add_argument('--disable-software-rasterizer')
        chrome_options.add_argument('--disable-setuid-sandbox')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--ignore-certificate-errors')
        chrome_options.add_argument('--ignore-ssl-errors')
        chrome_options.add_argument('--window-size=1920,1080')
        
        if headless:
            logger.info("Käytetään headless-moodia")
            chrome_options.add_argument("--headless=new")  # Uudempi headless-moodi
        
        # Set PDF download preferences
        if not download_dir:
            download_dir = os.getcwd()
            logger.info(f"Käytetään oletuslataushakemistoa: {download_dir}")
            
        prefs = {
            "download.default_directory": download_dir,
            "download.prompt_for_download": False,
            "plugins.always_open_pdf_externally": True,
            "download.directory_upgrade": True,
        }
        chrome_options.add_experimental_option("prefs", prefs)
        logger.info("PDF-latausasetukset konfiguroitu")
        
        # Initialize the Chrome WebDriver with the system's Chrome browser
        service = Service()
        logger.info("Alustetaan Chrome-palvelu...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("Chrome WebDriver alustettu onnistuneesti")
        return driver
    except Exception as e:
        logger.error(f"Virhe Chrome WebDriverin alustamisessa: {e}")
        logger.error(traceback.format_exc())
        raise

def is_valid_pdf(file_path):
    """
    Tarkistaa, onko PDF-tiedosto validi.
    
    Args:
        file_path (str): Tiedostopolku tarkistettavaan PDF-tiedostoon
        
    Returns:
        bool: True jos PDF on validi, False muuten
    """
    try:
        # Yritetään avata PDF PyPDF2:lla
        with open(file_path, 'rb') as f:
            try:
                reader = PyPDF2.PdfReader(f)
                # Tarkistetaan että vähintään 1 sivu
                if len(reader.pages) > 0:
                    return True
            except Exception as e:
                logger.error(f"PDF validointi epäonnistui: {e}")
                return False
        return False
    except Exception as e:
        logger.error(f"Tiedoston avaaminen validointia varten epäonnistui: {e}")
        return False

def download_pdf_with_retry(url, output_filename=None, headless=False, max_retries=3):
    """
    Lataa PDF-tiedosto uudelleenyrityksillä.
    
    Args:
        url (str): Etuovi.com kohteen URL
        output_filename (str, optional): Tiedostonimi PDF:lle
        headless (bool): Käytetäänkö headless-moodia
        max_retries (int): Maksimi uudelleenyritykset
        
    Returns:
        str: Polku ladattuun PDF-tiedostoon
    """
    retry_count = 0
    last_error = None
    
    while retry_count < max_retries:
        try:
            pdf_path = download_pdf(url, output_filename, headless)
            
            # Tarkista että PDF on validi
            if pdf_path and os.path.exists(pdf_path) and is_valid_pdf(pdf_path):
                logger.info(f"PDF ladattu ja validoitu onnistuneesti yrityskerralla {retry_count + 1}")
                return pdf_path
            else:
                raise Exception(f"Ladattu PDF ei ole validi: {pdf_path}")
                
        except Exception as e:
            retry_count += 1
            last_error = e
            logger.warning(f"PDF:n lataus epäonnistui (yritys {retry_count}/{max_retries}): {e}")
            
            # Odota ennen uutta yritystä (eksponentiaalinen backoff)
            wait_time = 2 ** retry_count
            logger.info(f"Odotetaan {wait_time} sekuntia ennen uutta yritystä...")
            time.sleep(wait_time)
    
    # Jos kaikki yritykset epäonnistuivat, kokeillaan vaihtoehtoista lataustapaa
    logger.error(f"Kaikki {max_retries} yritystä epäonnistuivat. Viimeisin virhe: {last_error}")
    
    try:
        # Kokeillaan suoraa latausta requests-kirjastolla
        logger.info(f"Kokeillaan vaihtoehtoista lataustapaa: suora HTTP-lataus...")
        if not output_filename:
            property_id = url.split('/')[-1].split('?')[0]  # Poista query-parametrit
            output_filename = f"etuovi_{property_id}.pdf"
            
        output_path = os.path.join(os.getcwd(), output_filename)
        
        response = requests.get(url, timeout=30)
        with open(output_path, "wb") as f:
            f.write(response.content)
            
        # Validate the PDF
        if is_valid_pdf(output_path):
            logger.info(f"PDF ladattu onnistuneesti vaihtoehtoisella tavalla: {output_path}")
            return output_path
        else:
            raise Exception("Vaihtoehtoinen lataus epäonnistui: Tiedosto ei ole validi PDF")
            
    except Exception as e:
        logger.error(f"Vaihtoehtoinen latausyritys epäonnistui: {e}")
        raise Exception(f"PDF:n lataus ei onnistunut useiden yritysten jälkeen: {str(last_error)}")

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
    logger.info(f"Aloitetaan PDF:n lataus URL:sta {url}")
    
    if not output_filename:
        # Extract property ID from URL for default filename
        property_id = url.split('/')[-1].split('?')[0]  # Poista query-parametrit
        output_filename = f"etuovi_{property_id}.pdf"
        logger.info(f"Luodaan oletustiedostonimi: {output_filename}")
    
    # Create a temporary download directory with unique identifier
    session_id = str(uuid.uuid4())
    timestamp = int(time.time())
    temp_download_dir = os.path.join(
        tempfile.gettempdir(),
        f"etuovi_download_{timestamp}_{session_id}"
    )
    os.makedirs(temp_download_dir, exist_ok=True)
    logger.info(f"Luotu väliaikainen lataushakemisto: {temp_download_dir}")
    
    driver = None
    try:
        driver = setup_driver(headless=headless, download_dir=temp_download_dir)
        
        logger.info(f"Navigoidaan osoitteeseen: {url}")
        driver.get(url)
        
        # Wait for the page to load
        logger.info("Odotetaan sivun latautumista...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logger.info("Sivu ladattu onnistuneesti")
        
        # Scroll down to make the PDF button visible (multiple scrolls to ensure it's in view)
        logger.info("Skrollataan sivua PDF-painikkeen löytämiseksi...")
        for i in range(5):  # Increased scroll attempts
            driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)
        
        # Find the "TULOSTA PDF" button using multiple strategies
        logger.info("Etsitään PDF-painiketta...")
        pdf_button = None
        
        # Strategy 1: Find by scanning all buttons for PDF-related content
        try:
            all_buttons = driver.find_elements(By.TAG_NAME, 'button')
            logger.info(f"Löydettiin {len(all_buttons)} painiketta")
            
            for button in all_buttons:
                try:
                    button_html = button.get_attribute("innerHTML").lower()
                    button_text = button.text.lower()
                    
                    # More comprehensive search criteria
                    if any(keyword in button_html or keyword in button_text 
                           for keyword in ["tulosta", "pdf", "print", "lataa"]):
                        pdf_button = button
                        logger.info("PDF-painike löydetty painikkeiden skannauksella")
                        break
                except Exception as e:
                    logger.warning(f"Painikkeen tarkistus epäonnistui: {e}")
                    continue
        except Exception as e:
            logger.error(f"Painikkeiden etsiminen epäonnistui: {e}")
        
        # Strategy 2: Try finding by XPath with multiple patterns
        if not pdf_button:
            xpath_patterns = [
                "//button[contains(., 'PDF')]",
                "//button[contains(., 'Tulosta')]",
                "//button[contains(., 'tulosta')]",
                "//a[contains(., 'PDF')]",
                "//div[contains(@class, 'pdf')]//button",
                "//div[contains(@class, 'print')]//button"
            ]
            
            for xpath in xpath_patterns:
                try:
                    elements = driver.find_elements(By.XPATH, xpath)
                    if elements:
                        pdf_button = elements[0]
                        logger.info(f"PDF-painike löydetty XPath:lla: {xpath}")
                        break
                except Exception as e:
                    logger.warning(f"XPath-haku epäonnistui: {xpath} - {e}")
        
        if not pdf_button:
            raise Exception("PDF-painiketta ei löytynyt sivulta")
        
        # Click the PDF button
        logger.info("Klikataan PDF-painiketta...")
        driver.execute_script("arguments[0].scrollIntoView(true);", pdf_button)
        time.sleep(2)  # Increased wait time
        
        # Try multiple click methods
        try:
            # Try normal click first
            pdf_button.click()
        except Exception as e:
            logger.warning(f"Normaali klikki epäonnistui: {e}")
            try:
                # Try JavaScript click if normal click fails
                driver.execute_script("arguments[0].click();", pdf_button)
                logger.info("Käytetty JavaScript-klikkiä")
            except Exception as js_e:
                logger.error(f"JavaScript-klikki epäonnistui: {js_e}")
                raise
        
        # Wait for the PDF to load in a new tab or iframe
        logger.info("Odotetaan PDF:n latautumista...")
        time.sleep(7)  # Increased wait time
        
        # Check if a new tab was opened
        if len(driver.window_handles) > 1:
            logger.info("Uusi välilehti avattu, siirrytään siihen")
            driver.switch_to.window(driver.window_handles[1])
        
        # Get the current URL (which might be the PDF URL)
        current_url = driver.current_url
        logger.info(f"Nykyinen URL klikkauksen jälkeen: {current_url}")
        
        # Wait for the download to complete
        logger.info("Odotetaan latauksen valmistumista...")
        max_wait_time = 45  # Increased maximum wait time
        start_time = time.time()
        
        while time.time() - start_time < max_wait_time:
            # Check if any PDF files have been downloaded
            pdf_files = glob.glob(os.path.join(temp_download_dir, "*.pdf"))
            
            if pdf_files:
                # Found a downloaded PDF file
                downloaded_file = pdf_files[0]  # Take the first PDF file found
                logger.info(f"Ladattu tiedosto löydetty: {downloaded_file}")
                
                # Validate PDF before copying
                if is_valid_pdf(downloaded_file):
                    # Copy the file to the desired output location
                    output_path = os.path.join(os.getcwd(), output_filename)
                    shutil.copy2(downloaded_file, output_path)
                    logger.info(f"PDF tallennettu polkuun: {output_path}")
                    
                    return os.path.abspath(output_path)
                else:
                    logger.warning(f"Ladattu PDF ei ole validi: {downloaded_file}")
                    # Delete invalid file and continue waiting
                    try:
                        os.remove(downloaded_file)
                        logger.info(f"Poistettu viallinen tiedosto: {downloaded_file}")
                    except Exception as e:
                        logger.warning(f"Viallisen tiedoston poistaminen epäonnistui: {e}")
            
            # If no file found yet, wait a bit and check again
            time.sleep(1)
        
        # If we reach here, no PDF file was found in the download directory
        # Try to download directly from the blob URL if available
        if "blob:" in current_url:
            logger.info(f"Ladattua tiedostoa ei löytynyt. Yritetään ladata blob-URL:sta: {current_url}")
            
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
                
                # Validate the PDF
                if is_valid_pdf(output_path):
                    logger.info(f"PDF tallennettu blob-URL:sta polkuun: {output_path}")
                    return os.path.abspath(output_path)
                else:
                    logger.warning(f"Blob-URL:sta ladattu PDF ei ole validi")
                    raise Exception("Blob-URL:sta ladattu PDF ei ole validi")
            else:
                raise Exception("PDF-sisällön purkaminen blob-URL:sta epäonnistui")
        else:
            # If it's a direct PDF URL, download it with requests
            logger.info(f"Ladattua tiedostoa ei löytynyt. Ladataan PDF suoraan URL:sta: {url}")
            
            # Kokeillaan kohteen URL:ia
            try:
                response = requests.get(url, stream=True, timeout=30)
                output_path = os.path.join(os.getcwd(), output_filename)
                
                with open(output_path, "wb") as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                
                # Validate the PDF
                if is_valid_pdf(output_path):
                    logger.info(f"PDF tallennettu suoraan URL:sta polkuun: {output_path}")
                    return os.path.abspath(output_path)
                else:
                    logger.warning(f"Suoraan URL:sta ladattu PDF ei ole validi")
                    raise Exception("Suoraan URL:sta ladattu PDF ei ole validi")
            except Exception as e:
                logger.error(f"Suora URL-lataus epäonnistui: {e}")
                raise
    
    except Exception as e:
        logger.error(f"Virhe PDF:n lataamisessa: {e}")
        logger.error(traceback.format_exc())
        raise
    
    finally:
        # Close the browser
        if driver:
            try:
                driver.quit()
                logger.info("Selain suljettu")
            except Exception as e:
                logger.warning(f"Selaimen sulkeminen epäonnistui: {e}")
        
        # Clean up the temporary download directory
        try:
            if os.path.exists(temp_download_dir) and os.path.isdir(temp_download_dir):
                shutil.rmtree(temp_download_dir)
                logger.info(f"Väliaikainen lataushakemisto poistettu: {temp_download_dir}")
        except Exception as e:
            logger.warning(f"Väliaikaisen lataushakemiston poistaminen epäonnistui: {e}")

def convert_pdf_to_text(pdf_path):
    """
    Convert a PDF file to text format.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        str: Path to the created text file
    """
    logger.info(f"Muunnetaan PDF tekstiksi: {pdf_path}")
    
    # Tarkista onko tiedosto olemassa
    if not os.path.exists(pdf_path):
        logger.error(f"PDF-tiedostoa ei löydy: {pdf_path}")
        raise FileNotFoundError(f"PDF-tiedostoa ei löydy: {pdf_path}")
    
    # Tarkista onko tiedosto tyhjä
    if os.path.getsize(pdf_path) == 0:
        logger.error(f"PDF-tiedosto on tyhjä: {pdf_path}")
        raise ValueError(f"PDF-tiedosto on tyhjä: {pdf_path}")
    
    try:
        # Create output text file path by changing extension
        text_path = os.path.splitext(pdf_path)[0] + '.txt'
        
        max_retries = 3
        retry_count = 0
        success = False
        
        while not success and retry_count < max_retries:
            try:
                # Open the PDF file
                with open(pdf_path, 'rb') as pdf_file:
                    # Create a PDF reader object
                    pdf_reader = PyPDF2.PdfReader(pdf_file)
                    
                    # Check if PDF has pages
                    if len(pdf_reader.pages) == 0:
                        raise ValueError(f"PDF ei sisällä sivuja: {pdf_path}")
                    
                    # Open text file for writing
                    with open(text_path, 'w', encoding='utf-8') as text_file:
                        # Extract text from each page and write to text file
                        for page_num in range(len(pdf_reader.pages)):
                            logger.info(f"Käsitellään sivu {page_num + 1}/{len(pdf_reader.pages)}")
                            page = pdf_reader.pages[page_num]
                            text = page.extract_text()
                            text_file.write(f"--- Page {page_num + 1} ---\n")
                            text_file.write(text if text else "Sivulta ei löytynyt tekstiä.")
                            text_file.write('\n\n')
                
                # Tarkista että tekstitiedosto luotiin
                if os.path.exists(text_path) and os.path.getsize(text_path) > 0:
                    success = True
                else:
                    logger.warning(f"Luotu tekstitiedosto on tyhjä: {text_path}")
                    retry_count += 1
                    time.sleep(1)
            
            except Exception as e:
                retry_count += 1
                logger.warning(f"PDF-muunnos epäonnistui (yritys {retry_count}/{max_retries}): {e}")
                if retry_count < max_retries:
                    time.sleep(2)
                else:
                    raise
        
        logger.info(f"PDF muunnettu onnistuneesti tekstiksi: {text_path}")
        return text_path
    
    except Exception as e:
        logger.error(f"Virhe PDF:n muuntamisessa tekstiksi: {e}")
        logger.error(traceback.format_exc())
        
        # Create a basic text file with error information if PDF processing fails
        text_path = os.path.splitext(pdf_path)[0] + '.txt'
        try:
            with open(text_path, 'w', encoding='utf-8') as text_file:
                text_file.write(f"PDF-KÄSITTELYVIRHE: {str(e)}\n\n")
                text_file.write(f"Tiedoston nimi: {os.path.basename(pdf_path)}\n")
                text_file.write(f"Tiedoston koko: {os.path.getsize(pdf_path)} tavua\n")
                text_file.write("PDF-tiedostoa ei voitu käsitellä. Käytä alkuperäistä PDF-tiedostoa manuaaliseen tarkasteluun.")
            
            logger.info(f"Luotu virhetietoja sisältävä tekstitiedosto: {text_path}")
            return text_path
        except Exception as write_error:
            logger.error(f"Virhe kirjoitettaessa virhetiedostoa: {write_error}")
            raise e

def main():
    """Main function to parse arguments and download the PDF."""
    parser = argparse.ArgumentParser(description="Download PDF from Etuovi.com property listing and convert to text")
    parser.add_argument("url", help="URL of the property listing")
    parser.add_argument("output", nargs="?", help="Output filename (optional)")
    parser.add_argument("--no-headless", action="store_true", help="Run in non-headless mode (shows browser UI)")
    parser.add_argument("--no-text", action="store_true", help="Skip converting PDF to text")
    args = parser.parse_args()
    
    try:
        logger.info(f"Aloitetaan PDF:n lataus URL:sta {args.url}")
        pdf_path = download_pdf_with_retry(args.url, args.output, headless=not args.no_headless)
        logger.info(f"PDF ladattu onnistuneesti: {pdf_path}")
        
        # Convert PDF to text unless --no-text flag is used
        if not args.no_text:
            text_path = convert_pdf_to_text(pdf_path)
            logger.info(f"Tekstitiedosto luotu: {text_path}")
        
        return 0
    except Exception as e:
        logger.error(f"PDF:n lataus tai muuntaminen tekstiksi epäonnistui: {e}")
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
