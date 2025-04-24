"""
Etuovi Dockling

This module provides functions for converting PDF files to markdown using the docling library.
"""

import logging
from typing import Optional
from docling.document_converter import DocumentConverter

def convert_pdf_to_markdown(pdf_path: str) -> Optional[str]:
    """
    Convert a PDF file to markdown text using the docling library.
    
    Args:
        pdf_path (str): Path to the PDF file to convert.
        
    Returns:
        Optional[str]: The markdown content if successful, None otherwise.
    """
    try:
        # Initialize the document converter
        converter = DocumentConverter()
        
        # Convert the PDF
        result = converter.convert(pdf_path)
        
        # Export to markdown
        markdown_content = result.document.export_to_markdown()
        
        # Return the markdown content
        return markdown_content
    except Exception as e:
        logging.error(f"Error converting PDF to markdown: {e}")
        return None

# Example usage (for testing purposes only)
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        markdown = convert_pdf_to_markdown(pdf_path)
        if markdown:
            print(markdown[:500] + "...")  # Print the first 500 characters
        else:
            print("Conversion failed")
    else:
        print("Usage: python etuovi_dockling.py <pdf_path>")