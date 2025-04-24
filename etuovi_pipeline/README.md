# Etuovi Pipeline

This module provides functionality for processing property listings from Etuovi.com.

## Features

- Downloads property information PDF from Etuovi listings
- Converts PDF to markdown format
- Integrates with the main application's API flow

## How it works

1. The pipeline takes an Etuovi property listing URL
2. Using Selenium, it navigates to the page and locates the "Print PDF" button
3. It clicks the button and downloads the PDF file
4. Using the docling library, it converts the PDF to markdown format
5. The markdown content is passed to the API for analysis

## Usage

```python
from etuovi_pipeline.etuovi_pipeline import process_etuovi_listing

# Process an Etuovi listing and get the path to the markdown file
markdown_path = process_etuovi_listing("https://www.etuovi.com/kohde/12345")

# Read the markdown content
with open(markdown_path, 'r', encoding='utf-8') as f:
    markdown_content = f.read()

# Now you can use this markdown_content for analysis
```

## Requirements

- selenium
- docling
- Chrome or Chromium browser installed on the system

## Configuration

The pipeline is configured to run in headless mode by default. If you encounter issues with the PDF button not being found, you can run it in non-headless mode for debugging:

```python
markdown_path = process_etuovi_listing(url, headless=False)
``` 