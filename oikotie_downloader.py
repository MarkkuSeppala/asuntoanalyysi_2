#!/usr/bin/env python3
import re
import os
import requests
import tempfile
from PyPDF2 import PdfReader
import unicodedata


def normalize_text(text):
    """Normalize Unicode text by replacing special characters."""
    # Replace common problematic characters
    replacements = {
        "Ã¤": "ä",
        "Ã¶": "ö",
        "Ã…": "Å",
        "Ã¥": "å",
        "â‚¬": "€",
        "mÂ²": "m²"
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text


def convert_to_showcase_url(url):
    """Convert an Oikotie property URL to its showcase PDF URL format.
    
    Args:
        url (str): Original Oikotie property URL
        
    Returns:
        str: URL for the showcase PDF
    """
    # Extract the property ID from the URL
    # The pattern should match /digits at the end of the URL
    match = re.search(r'/(\d+)/?$', url)
    if not match:
        raise ValueError(f"Invalid Oikotie URL format: {url}. Expected URL ending with a property ID.")
    
    property_id = match.group(1)
    print(f"Extracted property ID: {property_id}")
    return f"https://asunnot.oikotie.fi/nayttoesite/{property_id}"


def download_pdf(showcase_url, output_path=None):
    """Download the PDF from the showcase URL.
    
    Args:
        showcase_url (str): The showcase URL to download the PDF from
        output_path (str, optional): Path to save the PDF. If None, uses a temporary file.
        
    Returns:
        str: Path to the downloaded PDF file
    """
    print(f"Attempting to download PDF from: {showcase_url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        response = requests.get(showcase_url, headers=headers)
        
        # Check if the request was successful
        if response.status_code != 200:
            raise Exception(f"Failed to download PDF. Status code: {response.status_code}")
        
        # If no output path is specified, create a temporary file
        if output_path is None:
            temp_fd, output_path = tempfile.mkstemp(suffix='.pdf')
            os.close(temp_fd)
        
        # Write the PDF content to the file
        with open(output_path, 'wb') as f:
            f.write(response.content)
        
        print(f"PDF successfully downloaded to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error downloading PDF: {e}")
        raise


def extract_text_from_pdf(pdf_path):
    """Extract text from a PDF file.
    
    Args:
        pdf_path (str): Path to the PDF file
    
    Returns:
        str: Extracted text content
    """
    print(f"Extracting text from PDF: {pdf_path}")
    
    try:
        reader = PdfReader(pdf_path)
        text = ""
        
        # Extract text from each page
        for i, page in enumerate(reader.pages):
            print(f"Processing page {i+1}/{len(reader.pages)}")
            page_text = page.extract_text()
            text += page_text + "\n\n"
        
        # Normalize problematic characters
        normalized_text = normalize_text(text)
        
        return normalized_text
    except Exception as e:
        print(f"Error extracting text from PDF: {e}")
        raise


def process_oikotie_url(url):
    """Process an Oikotie URL to download the PDF and convert it to text.
    
    Args:
        url (str): Original Oikotie property URL
        
    Returns:
        str: Extracted text content
    """
    print(f"Processing Oikotie URL: {url}")
    pdf_path = None
    
    try:
        # Convert the URL to showcase format
        showcase_url = convert_to_showcase_url(url)
        
        # Download the PDF to a temporary file
        pdf_path = download_pdf(showcase_url)
        
        # Extract text from the PDF
        text_content = extract_text_from_pdf(pdf_path)
        
        return text_content
    except Exception as e:
        print(f"Error processing URL: {e}")
        raise
    finally:
        # Clean up: Delete the PDF file
        if pdf_path and os.path.exists(pdf_path):
            try:
                os.remove(pdf_path)
                print(f"Temporary PDF file deleted: {pdf_path}")
            except Exception as e:
                print(f"Warning: Failed to delete temporary PDF file: {e}")


def get_property_info(url, verbose=True):
    """Main function to get property information from an Oikotie URL.
    
    This is the recommended function to use when importing this module.
    
    Args:
        url (str): Original Oikotie property URL
        verbose (bool): Whether to print progress messages
        
    Returns:
        str: Property information as text
    """
    # Save the current print function
    original_print = print
    
    # If verbose is False, disable printing
    if not verbose:
        # Define a function that does nothing
        def silent_print(*args, **kwargs):
            pass
        # Replace the built-in print function with our silent version
        globals()['print'] = silent_print
    
    try:
        # Process the URL and get the property information
        return process_oikotie_url(url)
    finally:
        # Restore the original print function
        globals()['print'] = original_print


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python oikotie_downloader.py <oikotie_url> [output_text_path]")
        sys.exit(1)
    
    # Parse command line arguments
    url = sys.argv[1]
    output_text_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        print("\n=== Oikotie Property Downloader ===\n")
        text_content = process_oikotie_url(url)
        
        # If output path is provided, write to file
        if output_text_path:
            with open(output_text_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            print(f"\nText content written to: {output_text_path}")
        else:
            # Otherwise print to console
            print("\n=== Extracted Text Content ===\n")
            print(text_content)
        
        print("\nProcess completed successfully.")
    except Exception as e:
        print(f"\nError: {e}")
        sys.exit(1)
