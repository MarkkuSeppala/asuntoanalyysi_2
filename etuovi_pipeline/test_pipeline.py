#!/usr/bin/env python3
"""
Test script for the Etuovi pipeline.

This script allows you to test the Etuovi pipeline by providing an Etuovi URL.
It will download the PDF and convert it to markdown, then display the beginning
of the markdown content.

Usage:
    python test_pipeline.py <etuovi_url>

Example:
    python test_pipeline.py https://www.etuovi.com/kohde/12345
"""

import os
import sys
import argparse
from etuovi_pipeline.etuovi_pipeline import process_etuovi_listing

def test_pipeline(url, headless=True):
    """
    Test the Etuovi pipeline with a given URL.
    
    Args:
        url (str): The Etuovi URL to test.
        headless (bool): Whether to run in headless mode.
    """
    print(f"Testing Etuovi pipeline with URL: {url}")
    
    try:
        # Process the Etuovi listing
        markdown_path = process_etuovi_listing(url, headless=headless)
        
        print(f"\nProcessing complete. Markdown file saved at: {markdown_path}")
        
        # Read the markdown content
        with open(markdown_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        
        # Print the beginning of the markdown content
        preview_length = min(500, len(markdown_content))
        print(f"\nMarkdown content preview (first {preview_length} characters):\n")
        print(markdown_content[:preview_length] + "...")
        
        print(f"\nTotal markdown content length: {len(markdown_content)} characters")
        return True
    
    except Exception as e:
        print(f"\nError testing Etuovi pipeline: {e}")
        return False

def main():
    """Main function to parse arguments and run the test."""
    parser = argparse.ArgumentParser(description="Test the Etuovi pipeline")
    parser.add_argument("url", help="URL of the Etuovi property listing")
    parser.add_argument("--no-headless", action="store_true", help="Run in non-headless mode (shows browser UI)")
    args = parser.parse_args()
    
    success = test_pipeline(args.url, headless=not args.no_headless)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 