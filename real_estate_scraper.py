#!/usr/bin/env python3
"""
Real Estate Listing Scraper

This script extracts information from real estate listings on asunnot.oikotie.fi
and formats it into a structured markdown document for AI analysis.

The script is designed to be robust against website structure changes by using
multiple extraction methods and fallback mechanisms.

Usage:
    python real_estate_scraper.py <url> [-o OUTPUT_FILE]

Example:
    python real_estate_scraper.py https://asunnot.oikotie.fi/myytavat-asunnot/vantaa/23078097 -o listing.md

Author: AI Assistant
Date: April 2025
"""

import sys
import re
import argparse
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime
import traceback

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

class RealEstateScraper:
    """
    A class to scrape real estate listings from asunnot.oikotie.fi
    and format the data into a structured markdown document.
    
    This class implements multiple extraction strategies to be robust
    against website structure changes.
    """
    
    def __init__(self, url):
        """
        Initialize the scraper with the URL of the listing to scrape.
        
        Args:
            url (str): The URL of the real estate listing to scrape.
        """
        self.url = url
        self.soup = None
        # Initialize data structure to store extracted information
        self.data = {
            'basic_info': {},
            'price_info': {},
            'property_features': {},
            'building_info': {},
            'renovations': {
                'upcoming': [],
                'completed': []
            },
            'land_info': {},
            'location_info': {},
            'contact_info': {},
            'description': ''
        }
    
    def fetch_page(self):
        """
        Fetch the HTML content of the listing page and parse it with BeautifulSoup.
        
        Uses a comprehensive set of headers to mimic a real browser request
        and avoid being blocked by the website.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            # Set headers to mimic a real browser request
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept-Language': 'en-US,en;q=0.9,fi;q=0.8',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Cache-Control': 'max-age=0'
            }
            
            # Make the request with a timeout to avoid hanging
            response = requests.get(self.url, headers=headers, timeout=30)
            response.raise_for_status()  # Raise an exception for HTTP errors
            
            # Parse the HTML content with BeautifulSoup
            self.soup = BeautifulSoup(response.text, 'html.parser')
            return True
        
        except requests.RequestException as e:
            logger.error(f"Error fetching page: {e}")
            return False
    
    def extract_data(self):
        """
        Extract all relevant data from the parsed HTML.
        
        This method orchestrates the extraction of different types of information
        by calling specialized extraction methods for each category.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        if not self.soup:
            logger.error("No page content to extract data from. Call fetch_page() first.")
            return False
        
        try:
            # Extract different types of information using specialized methods
            self._extract_basic_info()
            self._extract_price_info()
            self._extract_property_features()
            self._extract_building_info()
            self._extract_renovations()
            self._extract_land_info()
            self._extract_location_info()
            self._extract_contact_info()
            self._extract_description()
            
            return True
        
        except Exception as e:
            logger.error(f"Error extracting data: {e}")
            logger.error(traceback.format_exc())  # Log the full traceback for debugging
            return False
    
    def _find_section_value(self, section_name):
        """
        Helper method to find a section value by its name using multiple strategies.
        
        This method implements several different approaches to find information
        in the HTML structure, making it robust against website structure changes.
        
        Args:
            section_name (str): The name of the section to find.
            
        Returns:
            str or None: The value of the section if found, None otherwise.
        """
        # Strategy 1: Try to find section by exact text match
        section = self.soup.find(string=re.compile(f"^{section_name}$", re.IGNORECASE))
        if section and section.parent and section.parent.find_next_sibling():
            return section.parent.find_next_sibling().get_text(strip=True)
        
        # Strategy 2: Try to find section by containing text
        section = self.soup.find(string=re.compile(section_name, re.IGNORECASE))
        if section and section.parent and section.parent.find_next_sibling():
            return section.parent.find_next_sibling().get_text(strip=True)
        
        # Strategy 3: Try to find in dt/dd structure (definition lists)
        dt = self.soup.find('dt', string=re.compile(section_name, re.IGNORECASE))
        if dt and dt.find_next('dd'):
            return dt.find_next('dd').get_text(strip=True)
        
        # Strategy 4: Try to find in table structure
        th = self.soup.find('th', string=re.compile(section_name, re.IGNORECASE))
        if th and th.find_next('td'):
            return th.find_next('td').get_text(strip=True)
        
        # Strategy 5: Try to find in div structure with specific class patterns
        for div in self.soup.find_all('div', class_=lambda c: c and ('label' in c or 'title' in c or 'header' in c)):
            if re.search(section_name, div.get_text(), re.IGNORECASE):
                next_div = div.find_next('div', class_=lambda c: c and ('value' in c or 'content' in c or 'data' in c))
                if next_div:
                    return next_div.get_text(strip=True)
        
        # Strategy 6: Try to find in any element with specific text
        for elem in self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'div', 'span']):
            if re.search(f"{section_name}[: ]", elem.get_text(), re.IGNORECASE):
                next_elem = elem.find_next(['p', 'div', 'span'])
                if next_elem:
                    return next_elem.get_text(strip=True)
        
        # No match found
        return None
    
    def _extract_basic_info(self):
        """
        Extract basic property information.
        
        This method extracts fundamental details about the property such as
        address, size, room configuration, condition, etc.
        """
        try:
            # Extract title/headline from h1
            title_elem = self.soup.find('h1')
            if title_elem:
                self.data['basic_info']['title'] = title_elem.get_text(strip=True)
            
            # Extract address from breadcrumbs or specific sections
            address_parts = []
            for link in self.soup.find_all('a'):
                href = link.get('href', '')
                # Look for links that might contain address components
                if any(term in href.lower() for term in ['jonsaksenkuja', '01600', 'vantaa']):
                    address_parts.append(link.get_text(strip=True))
            
            if address_parts:
                self.data['basic_info']['address'] = ', '.join(address_parts)
            
            # Define sections to search for with multiple search terms for each
            main_sections = {
                'district': ['Kaupunginosa', 'District', 'Neighborhood'],
                'property_id': ['Kohdenumero', 'Property ID', 'Reference number'],
                'floor': ['Kerros', 'Floor'],
                'living_area': ['Asuinpinta-ala', 'Living area', 'Size'],
                'total_area': ['Kokonaispinta-ala', 'Total area'],
                'room_configuration': ['Huoneiston kokoonpano', 'Room configuration', 'Rooms'],
                'rooms': ['Huoneita', 'Rooms', 'Number of rooms'],
                'condition': ['Kunto', 'Condition'],
                'availability': ['Lisätietoa vapautumisesta', 'Availability', 'Available'],
                'property_type': ['Asumistyyppi', 'Property type', 'Type'],
                'building_type': ['Rakennuksen tyyppi', 'Building type']
            }
            
            # Extract data for each section using multiple search terms
            for key, search_terms in main_sections.items():
                for term in search_terms:
                    value = self._find_section_value(term)
                    if value:
                        self.data['basic_info'][key] = value
                        break
            
            # Extract from structured data if available
            for div in self.soup.find_all('div'):
                text = div.get_text(strip=True)
                
                # Look for patterns in text content
                # Size pattern (e.g., "72 m²")
                if re.search(r'\d+\s*m²', text):
                    if 'living_area' not in self.data['basic_info']:
                        self.data['basic_info']['living_area'] = text
                
                # Floor pattern (e.g., "2/3")
                if re.search(r'\d+\s*/\s*\d+', text) and 'kerros' in text.lower():
                    if 'floor' not in self.data['basic_info']:
                        self.data['basic_info']['floor'] = text
                
                # Room configuration pattern (e.g., "3h, k, kph, wc")
                if re.search(r'\d+h', text) and ('k' in text or 'kph' in text or 'wc' in text):
                    if 'room_configuration' not in self.data['basic_info']:
                        self.data['basic_info']['room_configuration'] = text
            
            # Extract from header section
            header_text = ''
            header = self.soup.find('header') or self.soup.find('div', class_=lambda c: c and ('header' in c or 'title' in c))
            if header:
                header_text = header.get_text(strip=True)
                
                # Extract size from header
                size_match = re.search(r'(\d+)\s*m²', header_text)
                if size_match and 'living_area' not in self.data['basic_info']:
                    self.data['basic_info']['living_area'] = f"{size_match.group(1)} m²"
                
                # Extract room configuration from header
                room_match = re.search(r'(\d+h[,\s]+.*?(?:parv|wc|kph|s)\.?)', header_text)
                if room_match and 'room_configuration' not in self.data['basic_info']:
                    self.data['basic_info']['room_configuration'] = room_match.group(1)
            
            # Extract from any visible structured data with itemprop attributes
            for elem in self.soup.find_all(['div', 'span']):
                if elem.get('itemprop') == 'address':
                    if 'address' not in self.data['basic_info']:
                        self.data['basic_info']['address'] = elem.get_text(strip=True)
                
                if elem.get('itemprop') == 'numberOfRooms':
                    if 'rooms' not in self.data['basic_info']:
                        self.data['basic_info']['rooms'] = elem.get_text(strip=True)
            
            # Try to extract from the page content directly using regex patterns
            page_content = self.soup.get_text()
            
            # District/Neighborhood pattern
            district_match = re.search(r'Kaupunginosa:?\s*([A-ZÄÖÅa-zäöå\s-]+)', page_content)
            if district_match and 'district' not in self.data['basic_info']:
                self.data['basic_info']['district'] = district_match.group(1).strip()
            
            # Property ID pattern
            id_match = re.search(r'Kohdenumero:?\s*(\d+)', page_content)
            if id_match and 'property_id' not in self.data['basic_info']:
                self.data['basic_info']['property_id'] = id_match.group(1).strip()
            
            # If we still don't have address, try to construct it from URL
            if 'address' not in self.data['basic_info']:
                url_parts = self.url.split('/')
                if len(url_parts) >= 2:
                    location = url_parts[-2].replace('-', ' ').title()
                    self.data['basic_info']['address'] = f"Address in {location}"
            
            # If we have the title but not room configuration, try to extract from title
            if 'title' in self.data['basic_info'] and 'room_configuration' not in self.data['basic_info']:
                title = self.data['basic_info']['title']
                room_match = re.search(r'(\d+h[,\s]+.*?(?:parv|wc|kph|s)\.?)', title)
                if room_match:
                    self.data['basic_info']['room_configuration'] = room_match.group(1)
        
        except Exception as e:
            logger.error(f"Error extracting basic info: {e}")
            logger.error(traceback.format_exc())
    
    def _extract_price_info(self):
        """
        Extract price information.
        
        This method extracts all price-related details such as asking price,
        debt-free price, monthly fees, etc.
        """
        try:
            # Define price-related sections to search for with multiple search terms for each
            price_sections = {
                'asking_price': ['Myyntihinta', 'Asking price', 'Price'],
                'debt_free_price': ['Velaton hinta', 'Debt-free price', 'Total price'],
                'price_per_sqm': ['Neliöhinta', 'Price per m²', 'Price/m²'],
                'debt_portion': ['Velkaosuus', 'Debt portion', 'Loan share'],
                'maintenance_fee': ['Hoitovastike', 'Maintenance fee', 'Maintenance charge'],
                'capital_charge': ['Pääomavastike', 'Capital charge', 'Finance charge'],
                'renovation_charge': ['Korjausvastike', 'Renovation charge', 'Repair charge'],
                'total_monthly_fee': ['Yhtiövastike yhteensä', 'Total monthly fee', 'Total charge'],
                'water_fee': ['Vesimaksun lisätiedot', 'Water fee', 'Water charge'],
                'other_costs': ['Muut kustannukset', 'Other costs', 'Additional costs']
            }
            
            # Extract data for each section using multiple search terms
            for key, search_terms in price_sections.items():
                for term in search_terms:
                    value = self._find_section_value(term)
                    if value:
                        self.data['price_info'][key] = value
                        break
            
            # Look for price in header or prominent positions
            for elem in self.soup.find_all(['h1', 'h2', 'h3', 'div']):
                text = elem.get_text(strip=True)
                
                # Look for price patterns (e.g., "150 000 €")
                price_match = re.search(r'(\d{1,3}(?:\s*\d{3})*)\s*€', text)
                if price_match:
                    price_value = price_match.group(1).replace(' ', '')
                    
                    # Determine which price field it is based on context
                    if 'velaton' in text.lower() and 'debt_free_price' not in self.data['price_info']:
                        self.data['price_info']['debt_free_price'] = f"{price_value} €"
                    elif 'myynti' in text.lower() and 'asking_price' not in self.data['price_info']:
                        self.data['price_info']['asking_price'] = f"{price_value} €"
                    elif 'asking_price' not in self.data['price_info'] and 'debt_free_price' not in self.data['price_info']:
                        self.data['price_info']['asking_price'] = f"{price_value} €"
            
            # Extract from page content directly using regex patterns
            page_content = self.soup.get_text()
            
            # Price per square meter pattern
            sqm_price_match = re.search(r'(\d{1,3}(?:\s*\d{3})*)\s*€\s*/\s*m²', page_content)
            if sqm_price_match and 'price_per_sqm' not in self.data['price_info']:
                self.data['price_info']['price_per_sqm'] = f"{sqm_price_match.group(1).replace(' ', '')} €/m²"
            
            # Maintenance fee pattern
            maint_fee_match = re.search(r'Hoitovastike:?\s*(\d+(?:[,.]\d+)?)\s*€\s*(?:/\s*kk)?', page_content)
            if maint_fee_match and 'maintenance_fee' not in self.data['price_info']:
                self.data['price_info']['maintenance_fee'] = f"{maint_fee_match.group(1)} €/kk"
            
            # Water fee pattern
            water_fee_match = re.search(r'Vesimaksu:?\s*(.*?)(?:\.|€|/hlö)', page_content)
            if water_fee_match and 'water_fee' not in self.data['price_info']:
                self.data['price_info']['water_fee'] = water_fee_match.group(1).strip()
        
        except Exception as e:
            logger.error(f"Error extracting price info: {e}")
            logger.error(traceback.format_exc())
    
    def _extract_property_features(self):
        """
        Extract property features.
        
        This method extracts details about the property's features such as
        kitchen equipment, bathroom facilities, balcony, storage, sauna, etc.
        """
        try:
            # Define feature-related sections to search for with multiple search terms for each
            feature_sections = {
                'kitchen': ['Keittiön varusteet', 'Kitchen equipment', 'Kitchen features'],
                'balcony': ['Parveke', 'Balcony'],
                'balcony_details': ['Parvekkeen lisätiedot', 'Balcony details', 'Additional balcony info'],
                'bathroom': ['Kylpyhuoneen varusteet', 'Bathroom equipment', 'Bathroom features'],
                'storage': ['Säilytystilat', 'Storage spaces', 'Storage'],
                'sauna': ['Asunnossa sauna', 'Sauna', 'Private sauna'],
                'sauna_details': ['Saunan lisätiedot', 'Sauna details', 'Additional sauna info'],
                'kitchen_floor': ['Keittiön lattia', 'Kitchen floor'],
                'kitchen_wall': ['Keittiön seinä', 'Kitchen wall'],
                'living_room_floor': ['Olohuoneen lattia', 'Living room floor'],
                'living_room_wall': ['Olohuoneen seinät', 'Living room walls'],
                'bedroom_floor': ['Makuuhuoneen lattia', 'Bedroom floor'],
                'bedroom_wall': ['Makuuhuoneen seinät', 'Bedroom walls'],
                'bathroom_floor': ['Kylpyhuoneen lattia', 'Bathroom floor'],
                'bathroom_wall': ['Kylpyhuoneen seinät', 'Bathroom walls']
            }
            
            # Extract data for each section using multiple search terms
            for key, search_terms in feature_sections.items():
                for term in search_terms:
                    value = self._find_section_value(term)
                    if value:
                        self.data['property_features'][key] = value
                        break
            
            # Combine balcony details if both fields exist
            if 'balcony' in self.data['property_features'] and 'balcony_details' in self.data['property_features']:
                self.data['property_features']['balcony'] = f"{self.data['property_features']['balcony']} - {self.data['property_features']['balcony_details']}"
                del self.data['property_features']['balcony_details']
            
            # Combine sauna details if both fields exist
            if 'sauna' in self.data['property_features'] and 'sauna_details' in self.data['property_features']:
                self.data['property_features']['sauna'] = f"{self.data['property_features']['sauna']} - {self.data['property_features']['sauna_details']}"
                del self.data['property_features']['sauna_details']
            
            # Extract from page content directly using regex patterns
            page_content = self.soup.get_text()
            
            # Check for sauna
            if 'sauna' not in self.data['property_features']:
                if re.search(r'sauna', page_content, re.IGNORECASE):
                    self.data['property_features']['sauna'] = 'Kyllä'
            
            # Check for balcony
            if 'balcony' not in self.data['property_features']:
                if re.search(r'parveke', page_content, re.IGNORECASE):
                    self.data['property_features']['balcony'] = 'Kyllä'
            
            # Extract materials from description if not found elsewhere
            description_paragraphs = []
            for p in self.soup.find_all('p')[:10]:  # Look in first 10 paragraphs
                description_paragraphs.append(p.get_text(strip=True))
            
            description_text = ' '.join(description_paragraphs)
            
            # Kitchen features pattern
            if 'kitchen' not in self.data['property_features']:
                kitchen_match = re.search(r'Keittiö(?:ssä|n)?\s+([^.]+)', description_text, re.IGNORECASE)
                if kitchen_match:
                    self.data['property_features']['kitchen'] = kitchen_match.group(1).strip()
            
            # Bathroom features pattern
            if 'bathroom' not in self.data['property_features']:
                bathroom_match = re.search(r'Kylpyhuone(?:essa|n)?\s+([^.]+)', description_text, re.IGNORECASE)
                if bathroom_match:
                    self.data['property_features']['bathroom'] = bathroom_match.group(1).strip()
        
        except Exception as e:
            logger.error(f"Error extracting property features: {e}")
            logger.error(traceback.format_exc())
    
    def _extract_building_info(self):
        """
        Extract building information.
        
        This method extracts details about the building such as name, type,
        construction year, number of apartments, floors, etc.
        """
        try:
            # Define building-related sections to search for with multiple search terms for each
            building_sections = {
                'name': ['Taloyhtiön nimi', 'Building name', 'Housing company'],
                'type': ['Rakennuksen tyyppi', 'Building type'],
                'construction_year': ['Rakennusvuosi', 'Construction year', 'Built'],
                'use_year': ['Rakennuksen käyttöönottovuosi', 'Year of use', 'Completed'],
                'apartments': ['Huoneistojen lukumäärä', 'Number of apartments', 'Units'],
                'floors': ['Kerroksia', 'Floors', 'Number of floors'],
                'elevator': ['Hissi', 'Elevator', 'Lift'],
                'material': ['Rakennusmateriaali', 'Building material', 'Material'],
                'roof_material': ['Kattomateriaali', 'Roof material'],
                'roof_type': ['Kattotyyppi', 'Roof type'],
                'energy_class': ['Energialuokka', 'Energy class', 'Energy rating'],
                'ventilation': ['Ilmastointijärjestelmä', 'Ventilation system', 'Ventilation'],
                'heating': ['Lämmitys', 'Heating system', 'Heating'],
                'antenna': ['Kiinteistön antennijärjestelmä', 'Antenna system', 'TV system']
            }
            
            # Extract data for each section using multiple search terms
            for key, search_terms in building_sections.items():
                for term in search_terms:
                    value = self._find_section_value(term)
                    if value:
                        self.data['building_info'][key] = value
                        break
            
            # Extract from page content directly using regex patterns
            page_content = self.soup.get_text()
            
            # Building name pattern
            building_name_match = re.search(r'Taloyhtiön nimi:?\s*([A-ZÄÖÅa-zäöå\s]+)', page_content)
            if building_name_match and 'name' not in self.data['building_info']:
                self.data['building_info']['name'] = building_name_match.group(1).strip()
            
            # Construction year pattern
            year_match = re.search(r'Rakennusvuosi:?\s*(\d{4})', page_content)
            if year_match and 'construction_year' not in self.data['building_info']:
                self.data['building_info']['construction_year'] = year_match.group(1)
            
            # Building type pattern
            building_type_match = re.search(r'Rakennuksen tyyppi:?\s*([A-ZÄÖÅa-zäöå\s]+)', page_content)
            if building_type_match and 'type' not in self.data['building_info']:
                self.data['building_info']['type'] = building_type_match.group(1).strip()
            
            # Look for structured data in specific sections
            for div in self.soup.find_all('div'):
                text = div.get_text(strip=True)
                
                # Construction year pattern (e.g., "1979")
                if re.search(r'19\d\d|20\d\d', text) and len(text) < 10:
                    if 'construction_year' not in self.data['building_info']:
                        self.data['building_info']['construction_year'] = text
                
                # Building type pattern
                if re.search(r'kerrostalo|rivitalo|omakotitalo', text.lower()) and len(text) < 20:
                    if 'type' not in self.data['building_info']:
                        self.data['building_info']['type'] = text
        
        except Exception as e:
            logger.error(f"Error extracting building info: {e}")
            logger.error(traceback.format_exc())
    
    def _extract_renovations(self):
        """
        Extract renovation information.
        
        This method extracts details about upcoming and completed renovations
        in the building, including years and descriptions.
        """
        try:
            # Find upcoming renovations section
            upcoming_renovations_section = None
            for term in ['Tulevat remontit', 'Upcoming renovations', 'Future renovations']:
                section = self.soup.find(string=re.compile(term, re.IGNORECASE))
                if section and section.parent:
                    upcoming_renovations_section = section.parent.find_next_sibling()
                    if upcoming_renovations_section:
                        break
            
            if upcoming_renovations_section:
                upcoming_text = upcoming_renovations_section.get_text(strip=True)
                
                # Try to parse year-based renovations using regex pattern
                year_pattern = re.compile(r'(\d{4})[:\s-]+(.*?)(?=\d{4}|$)', re.DOTALL)
                matches = year_pattern.findall(upcoming_text)
                
                if matches:
                    for year, description in matches:
                        self.data['renovations']['upcoming'].append({
                            'year': year.strip(),
                            'description': description.strip()
                        })
                else:
                    # If no year pattern found, store the whole text
                    self.data['renovations']['upcoming'].append({
                        'year': 'Upcoming',
                        'description': upcoming_text
                    })
            
            # Find completed renovations section
            completed_renovations_section = None
            for term in ['Tehdyt remontit', 'Completed renovations', 'Past renovations']:
                section = self.soup.find(string=re.compile(term, re.IGNORECASE))
                if section and section.parent:
                    completed_renovations_section = section.parent.find_next_sibling()
                    if completed_renovations_section:
                        break
            
            if completed_renovations_section:
                completed_text = completed_renovations_section.get_text(strip=True)
                
                # Try to parse year-based renovations using regex pattern
                year_pattern = re.compile(r'(\d{4})[:\s-]+(.*?)(?=\d{4}|$)', re.DOTALL)
                matches = year_pattern.findall(completed_text)
                
                if matches:
                    for year, description in matches:
                        self.data['renovations']['completed'].append({
                            'year': year.strip(),
                            'description': description.strip()
                        })
                else:
                    # If no year pattern found, store the whole text
                    self.data['renovations']['completed'].append({
                        'year': 'Completed',
                        'description': completed_text
                    })
            
            # If we still don't have renovations, try to extract from page content
            if not self.data['renovations']['upcoming'] and not self.data['renovations']['completed']:
                page_content = self.soup.get_text()
                
                # Look for renovation sections in the content using regex pattern
                renovation_pattern = re.compile(r'(Tulevat|Tehdyt) remontit:?\s*(.*?)(?=Tulevat remontit|Tehdyt remontit|$)', re.DOTALL | re.IGNORECASE)
                renovation_matches = renovation_pattern.findall(page_content)
                
                for renovation_type, description in renovation_matches:
                    if 'tulev' in renovation_type.lower():
                        self.data['renovations']['upcoming'].append({
                            'year': 'Upcoming',
                            'description': description.strip()
                        })
                    elif 'tehd' in renovation_type.lower():
                        self.data['renovations']['completed'].append({
                            'year': 'Completed',
                            'description': description.strip()
                        })
        
        except Exception as e:
            logger.error(f"Error extracting renovations: {e}")
            logger.error(traceback.format_exc())
    
    def _extract_land_info(self):
        """
        Extract land information.
        
        This method extracts details about the land such as plot size,
        plot ownership, zoning information, etc.
        """
        try:
            # Define land-related sections to search for with multiple search terms for each
            land_sections = {
                'plot_size': ['Tontin pinta-ala', 'Plot size', 'Lot size'],
                'plot_ownership': ['Tontin omistus', 'Plot ownership', 'Land tenure'],
                'zoning': ['Kaavoitustiedot', 'Zoning information', 'Planning information'],
                'zoning_status': ['Kaavatilanne', 'Zoning status', 'Planning status']
            }
            
            # Extract data for each section using multiple search terms
            for key, search_terms in land_sections.items():
                for term in search_terms:
                    value = self._find_section_value(term)
                    if value:
                        self.data['land_info'][key] = value
                        break
            
            # Extract from page content directly using regex patterns
            page_content = self.soup.get_text()
            
            # Plot size pattern
            plot_size_match = re.search(r'Tontin pinta-ala:?\s*(\d+(?:[,.]\d+)?\s*m²)', page_content)
            if plot_size_match and 'plot_size' not in self.data['land_info']:
                self.data['land_info']['plot_size'] = plot_size_match.group(1)
            
            # Plot ownership pattern
            plot_ownership_match = re.search(r'Tontin omistus:?\s*([A-ZÄÖÅa-zäöå\s]+)', page_content)
            if plot_ownership_match and 'plot_ownership' not in self.data['land_info']:
                self.data['land_info']['plot_ownership'] = plot_ownership_match.group(1).strip()
            
            # Check for "oma tontti" in description
            if 'plot_ownership' not in self.data['land_info']:
                if re.search(r'oma(?:lla)? tonti(?:lla)?', page_content, re.IGNORECASE):
                    self.data['land_info']['plot_ownership'] = 'Oma'
        
        except Exception as e:
            logger.error(f"Error extracting land info: {e}")
            logger.error(traceback.format_exc())
    
    def _extract_location_info(self):
        """
        Extract location information.
        
        This method extracts details about the location such as transportation
        connections, nearby services, etc.
        """
        try:
            # Define location-related sections to search for with multiple search terms for each
            location_sections = {
                'transportation': ['Liikenneyhteydet', 'Transportation', 'Public transport'],
                'services': ['Palvelut', 'Services', 'Amenities'],
                'additional_info': ['Lisätietoa alueesta', 'Additional location info', 'Area information']
            }
            
            # Extract data for each section using multiple search terms
            for key, search_terms in location_sections.items():
                for term in search_terms:
                    value = self._find_section_value(term)
                    if value:
                        self.data['location_info'][key] = value
                        break
            
            # Extract from description paragraphs
            description_paragraphs = []
            for p in self.soup.find_all('p')[:10]:  # Look in first 10 paragraphs
                description_paragraphs.append(p.get_text(strip=True))
            
            description_text = ' '.join(description_paragraphs)
            
            # Transportation pattern
            if 'transportation' not in self.data['location_info']:
                transport_match = re.search(r'(?:yhteydet|liikenne|bussi|juna|metro).*?(?:\.|$)', description_text, re.IGNORECASE)
                if transport_match:
                    self.data['location_info']['transportation'] = transport_match.group(0).strip()
            
            # Services pattern
            if 'services' not in self.data['location_info']:
                services_match = re.search(r'(?:palvelut|kaupat|koulut|päiväkodit).*?(?:\.|$)', description_text, re.IGNORECASE)
                if services_match:
                    self.data['location_info']['services'] = services_match.group(0).strip()
        
        except Exception as e:
            logger.error(f"Error extracting location info: {e}")
            logger.error(traceback.format_exc())
    
    def _extract_contact_info(self):
        """
        Extract contact information.
        
        This method extracts details about the contact person such as
        agent name, phone number, email, agency, viewing times, etc.
        """
        try:
            # Look for contact information in the page content
            page_content = self.soup.get_text()
            
            # Extract agent name using regex pattern
            agent_match = re.search(r'(?:Tiedustelut|Esittelyt|Välittäjä)(?:\s+ja\s+esittelyt)?:?\s*([A-ZÄÖÅa-zäöå\s-]+)', page_content)
            if agent_match:
                self.data['contact_info']['agent'] = agent_match.group(1).strip()
            
            # Extract phone number using regex pattern
            phone_match = re.search(r'(?:\+\d{1,3}[-\s]?)?(?:0\d{1,2}[-\s]?)?\d{3,4}[-\s]?\d{3,4}', page_content)
            if phone_match:
                self.data['contact_info']['phone'] = phone_match.group(0)
            
            # Extract email using regex pattern
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', page_content)
            if email_match:
                self.data['contact_info']['email'] = email_match.group(0)
            
            # Extract agency name using regex pattern
            agency_match = re.search(r'(?:RE/MAX|Kiinteistömaailma|OP Koti|Huoneistokeskus|SKV|Habita|Bo)[\s\w]+', page_content)
            if agency_match:
                self.data['contact_info']['agency'] = agency_match.group(0).strip()
            
            # Extract viewing times
            viewing_section = self.soup.find(string=re.compile('Seuraavat esittelyt', re.IGNORECASE))
            if viewing_section:
                viewing_times = []
                
                # Try to find list items
                if viewing_section.parent:
                    ul = viewing_section.parent.find_next('ul')
                    if ul:
                        for li in ul.find_all('li'):
                            viewing_times.append(li.get_text(strip=True))
                
                # If no list items found, try to find paragraphs
                if not viewing_times:
                    viewing_match = re.search(r'Seuraavat esittelyt:?\s*(.*?)(?=\n\n|\Z)', page_content, re.DOTALL)
                    if viewing_match:
                        viewing_text = viewing_match.group(1).strip()
                        for line in viewing_text.split('\n'):
                            if line.strip():
                                viewing_times.append(line.strip())
                
                if viewing_times:
                    self.data['contact_info']['viewing_times'] = viewing_times
        
        except Exception as e:
            logger.error(f"Error extracting contact info: {e}")
            logger.error(traceback.format_exc())
    
    def _extract_description(self):
        """
        Extract property description.
        
        This method extracts the main description text of the property.
        """
        try:
            # Find description paragraphs
            description_paragraphs = []
            
            # Look for paragraphs that are likely part of the description
            for p in self.soup.find_all('p'):
                text = p.get_text(strip=True)
                
                # Skip short paragraphs, likely not part of description
                if len(text) < 30:
                    continue
                
                # Skip paragraphs that look like contact info
                if re.search(r'@|puh|tel|yhteydenotto', text.lower()):
                    continue
                
                # Skip paragraphs that look like viewing times
                if re.search(r'esittely|näyttö', text.lower()) and re.search(r'\d{1,2}\.\d{1,2}', text):
                    continue
                
                description_paragraphs.append(text)
            
            # If we found paragraphs, join them
            if description_paragraphs:
                self.data['description'] = '\n\n'.join(description_paragraphs)
            else:
                # If no paragraphs found, try to extract from any text content
                main_content = self.soup.find('main') or self.soup.find('article') or self.soup.find('div', class_=lambda c: c and ('content' in c or 'main' in c))
                
                if main_content:
                    # Extract text content
                    content_text = main_content.get_text(strip=True)
                    
                    # Try to find description section using regex pattern
                    description_match = re.search(r'^(.*?)(?:Perustiedot|Hinta|Seuraavat esittelyt)', content_text, re.DOTALL | re.IGNORECASE)
                    if description_match:
                        self.data['description'] = description_match.group(1).strip()
        
        except Exception as e:
            logger.error(f"Error extracting description: {e}")
            logger.error(traceback.format_exc())
    
    def format_to_markdown(self):
        """
        Format the extracted data into a structured markdown document.
        
        This method organizes all the extracted data into a well-structured
        markdown document that can be easily fed into a generative AI system.
        
        Returns:
            str: The formatted markdown document.
        """
        try:
            md = []
            
            # Title section
            if 'title' in self.data['basic_info']:
                md.append(f"# {self.data['basic_info']['title']}")
            elif 'address' in self.data['basic_info'] and 'room_configuration' in self.data['basic_info']:
                md.append(f"# {self.data['basic_info']['address']} - {self.data['basic_info']['room_configuration']}")
            elif 'address' in self.data['basic_info']:
                md.append(f"# {self.data['basic_info']['address']}")
            else:
                md.append("# Real Estate Listing")
            
            md.append("")
            
            # Basic Information section
            md.append("## Perustiedot")
            
            if 'address' in self.data['basic_info']:
                md.append(f"- **Osoite:** {self.data['basic_info']['address']}")
            
            if 'district' in self.data['basic_info']:
                md.append(f"- **Alue:** {self.data['basic_info']['district']}")
            
            if 'building_type' in self.data['basic_info']:
                md.append(f"- **Rakennuksen tyyppi:** {self.data['basic_info']['building_type']}")
            elif 'type' in self.data['building_info']:
                md.append(f"- **Rakennuksen tyyppi:** {self.data['building_info']['type']}")
            
            if 'living_area' in self.data['basic_info']:
                md.append(f"- **Kokonaispinta-ala:** {self.data['basic_info']['living_area']}")
            
            if 'room_configuration' in self.data['basic_info']:
                md.append(f"- **Huoneita:** {self.data['basic_info']['room_configuration']}")
            elif 'rooms' in self.data['basic_info']:
                md.append(f"- **Huoneita:** {self.data['basic_info']['rooms']}")
            
            if 'floor' in self.data['basic_info']:
                md.append(f"- **Kerros:** {self.data['basic_info']['floor']}")
            
            if 'condition' in self.data['basic_info']:
                md.append(f"- **Kunto:** {self.data['basic_info']['condition']}")
            
            if 'construction_year' in self.data['building_info']:
                md.append(f"- **Rakennusvuosi:** {self.data['building_info']['construction_year']}")
            
            if 'availability' in self.data['basic_info']:
                md.append(f"- **Vapautuu:** {self.data['basic_info']['availability']}")
            
            if 'property_id' in self.data['basic_info']:
                md.append(f"- **Oikotien kohdenumero:** {self.data['basic_info']['property_id']}")
            
            md.append("")
            
            # Price Information section
            md.append("## Hinta")
            
            if 'asking_price' in self.data['price_info']:
                md.append(f"- **Myyntihinta:** {self.data['price_info']['asking_price']}")
            
            if 'debt_free_price' in self.data['price_info']:
                md.append(f"- **Velaton hinta:** {self.data['price_info']['debt_free_price']}")
            
            if 'price_per_sqm' in self.data['price_info']:
                md.append(f"- **Neliöhinta:** {self.data['price_info']['price_per_sqm']}")
            
            if 'debt_portion' in self.data['price_info']:
                md.append(f"- **Velkaosuus:** {self.data['price_info']['debt_portion']}")
            
            md.append("- **Kuukausikustannukset:**")
            
            if 'maintenance_fee' in self.data['price_info']:
                md.append(f"  - Hoitovastike: {self.data['price_info']['maintenance_fee']}")
            
            if 'capital_charge' in self.data['price_info']:
                md.append(f"  - Pääomavastike: {self.data['price_info']['capital_charge']}")
            
            if 'renovation_charge' in self.data['price_info']:
                md.append(f"  - Korjausvastike: {self.data['price_info']['renovation_charge']}")
            
            if 'total_monthly_fee' in self.data['price_info']:
                md.append(f"  - Yhtiövastike yhteensä: {self.data['price_info']['total_monthly_fee']}")
            
            if 'water_fee' in self.data['price_info']:
                md.append(f"  - Vesimaksun lisätiedot: {self.data['price_info']['water_fee']}")
            
            if 'other_costs' in self.data['price_info']:
                md.append(f"  - Muut kustannukset: {self.data['price_info']['other_costs']}")
            
            md.append("")
            
            # Property Features section
            md.append("## Asunnon ominaisuudet")
            
            if 'kitchen' in self.data['property_features']:
                md.append(f"- **Keittiö:** {self.data['property_features']['kitchen']}")
            
            if 'bathroom' in self.data['property_features']:
                md.append(f"- **Pesuhuone:** {self.data['property_features']['bathroom']}")
            
            if 'balcony' in self.data['property_features']:
                md.append(f"- **Parveke:** {self.data['property_features']['balcony']}")
            
            if 'storage' in self.data['property_features']:
                md.append(f"- **Säilytystila:** {self.data['property_features']['storage']}")
            
            if 'sauna' in self.data['property_features']:
                md.append(f"- **Sauna:** {self.data['property_features']['sauna']}")
            
            # Materials subsection
            md.append("- **Materiaalit:**")
            
            if 'kitchen_floor' in self.data['property_features'] or 'kitchen_wall' in self.data['property_features']:
                kitchen_floor = self.data['property_features'].get('kitchen_floor', 'N/A')
                kitchen_wall = self.data['property_features'].get('kitchen_wall', 'N/A')
                md.append(f"  - Keittiö: Lattia: {kitchen_floor}, Seinät: {kitchen_wall}")
            
            if 'living_room_floor' in self.data['property_features'] or 'living_room_wall' in self.data['property_features']:
                living_room_floor = self.data['property_features'].get('living_room_floor', 'N/A')
                living_room_wall = self.data['property_features'].get('living_room_wall', 'N/A')
                md.append(f"  - Parveke: Lattia: {living_room_floor}, Seinät: {living_room_wall}")
            
            if 'bedroom_floor' in self.data['property_features'] or 'bedroom_wall' in self.data['property_features']:
                bedroom_floor = self.data['property_features'].get('bedroom_floor', 'N/A')
                bedroom_wall = self.data['property_features'].get('bedroom_wall', 'N/A')
                md.append(f"  - Huone: Lattia: {bedroom_floor}, Seinät: {bedroom_wall}")
            
            if 'bathroom_floor' in self.data['property_features'] or 'bathroom_wall' in self.data['property_features']:
                bathroom_floor = self.data['property_features'].get('bathroom_floor', 'N/A')
                bathroom_wall = self.data['property_features'].get('bathroom_wall', 'N/A')
                md.append(f"  - Pesuhuone: Lattia: {bathroom_floor}, Seinät: {bathroom_wall}")
            
            md.append("")
            
            # Building Information section
            md.append("## Talon tiedot")
            
            if 'name' in self.data['building_info']:
                md.append(f"- **Taloyhtiön nimi:** {self.data['building_info']['name']}")
            
            if 'type' in self.data['building_info']:
                md.append(f"- **Rakennuksen tyyppi:** {self.data['building_info']['type']}")
            
            if 'construction_year' in self.data['building_info']:
                md.append(f"- **Rakennusvuosi:** {self.data['building_info']['construction_year']}")
            
            if 'apartments' in self.data['building_info']:
                md.append(f"- **Huoneistojen lukumäärä:** {self.data['building_info']['apartments']}")
            
            if 'floors' in self.data['building_info']:
                md.append(f"- **Kerroksia:** {self.data['building_info']['floors']}")
            
            if 'elevator' in self.data['building_info']:
                md.append(f"- **Hissi:** {self.data['building_info']['elevator']}")
            
            if 'material' in self.data['building_info']:
                md.append(f"- **Rakennusmateriaali:** {self.data['building_info']['material']}")
            
            if 'roof_type' in self.data['building_info'] or 'roof_material' in self.data['building_info']:
                roof_type = self.data['building_info'].get('roof_type', 'N/A')
                roof_material = self.data['building_info'].get('roof_material', 'N/A')
                md.append(f"- **Kattomateriaali:** {roof_type}, {roof_material}")
            
            if 'heating' in self.data['building_info']:
                md.append(f"- **Lämmitysjärjestelmä:** {self.data['building_info']['heating']}")
            
            if 'ventilation' in self.data['building_info']:
                md.append(f"- **Ilmanvaihto:** {self.data['building_info']['ventilation']}")
            
            if 'energy_class' in self.data['building_info']:
                md.append(f"- **Energialuokka:** {self.data['building_info']['energy_class']}")
            
            md.append("")
            
            # Renovations section
            md.append("## Remontit")
            
            if self.data['renovations']['upcoming']:
                md.append("- **Tulevat remontit:**")
                for renovation in self.data['renovations']['upcoming']:
                    md.append(f"  - {renovation['year']}: {renovation['description']}")
                md.append("")
            
            if self.data['renovations']['completed']:
                md.append("- **Tehdyt remontit:**")
                for renovation in self.data['renovations']['completed']:
                    md.append(f"  - {renovation['year']}: {renovation['description']}")
                md.append("")
            
            # Land Information section
            md.append("## Tontin tiedot")
            
            if 'plot_size' in self.data['land_info']:
                md.append(f"- **Tontin koko:** {self.data['land_info']['plot_size']}")
            
            if 'plot_ownership' in self.data['land_info']:
                md.append(f"- **Tontin omistus:** {self.data['land_info']['plot_ownership']}")
            
            if 'zoning' in self.data['land_info']:
                md.append(f"- **Kaavoitustiedot:** {self.data['land_info']['zoning']}")
            
            if 'zoning_status' in self.data['land_info']:
                md.append(f"- **Kaavoitustilanne:** {self.data['land_info']['zoning_status']}")
            
            md.append("")
            
            # Location and Services section
            md.append("## Aluetiedot")
            
            if 'transportation' in self.data['location_info']:
                md.append(f"- **Julkinen liikenne:** {self.data['location_info']['transportation']}")
            
            if 'services' in self.data['location_info']:
                md.append(f"- **Lähiympäristön palvelut:** {self.data['location_info']['services']}")
            
            if 'additional_info' in self.data['location_info']:
                md.append(f"- **Lisätiedot:** {self.data['location_info']['additional_info']}")
            
            md.append("")
            
            # Contact Information section
            md.append("## Yhteystiedot")
            
            if 'agent' in self.data['contact_info']:
                md.append(f"- **Kiinteistönvälittäjä:** {self.data['contact_info']['agent']}")
            
            if 'phone' in self.data['contact_info']:
                md.append(f"- **Puhelinnumero:** {self.data['contact_info']['phone']}")
            
            if 'email' in self.data['contact_info']:
                md.append(f"- **Sähköposti:** {self.data['contact_info']['email']}")
            
            if 'agency' in self.data['contact_info']:
                md.append(f"- **Välitysliike:** {self.data['contact_info']['agency']}")
            
            if 'viewing_times' in self.data['contact_info'] and self.data['contact_info']['viewing_times']:
                md.append("- **Näyttöajat:**")
                for time in self.data['contact_info']['viewing_times']:
                    md.append(f"  - {time}")
            
            md.append("")
            
            # Property Description section
            if self.data['description']:
                md.append("## Asunnon kuvaus")
                md.append(self.data['description'])
            
            # Add metadata
            md.append("")
            md.append("---")
            md.append(f"*Data extracted from {self.url} on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
            
            return '\n'.join(md)
        
        except Exception as e:
            logger.error(f"Error formatting to markdown: {e}")
            logger.error(traceback.format_exc())
            return f"Error formatting data: {e}"
    
    def save_to_file(self, filename):
        """
        Save the formatted markdown to a file.
        
        Args:
            filename (str): The name of the file to save to.
        
        Returns:
            bool: True if successful, False otherwise.
        """
        try:
            markdown = self.format_to_markdown()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            logger.info(f"Saved markdown to {filename}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving to file: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def run(self, output_file=None):
        """
        Run the complete scraping process.
        
        This method orchestrates the entire scraping process:
        1. Fetch the page
        2. Extract the data
        3. Format to markdown
        4. Save to file (if output_file is provided)
        
        Args:
            output_file (str, optional): The name of the file to save the output to.
                If None, the output is returned as a string.
        
        Returns:
            str or bool: The formatted markdown if output_file is None,
                otherwise True if successful, False otherwise.
        """
        if not self.fetch_page():
            logger.error("Failed to fetch page")
            return False
        
        if not self.extract_data():
            logger.error("Failed to extract data")
            return False
        
        if output_file:
            return self.save_to_file(output_file)
        else:
            return self.format_to_markdown()


def main():
    """
    Main function to run the script.
    
    This function parses command line arguments and runs the scraper.
    """
    parser = argparse.ArgumentParser(
        description='Scrape real estate listings from asunnot.oikotie.fi and format to markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  python real_estate_scraper.py https://asunnot.oikotie.fi/myytavat-asunnot/vantaa/23078097
  python real_estate_scraper.py https://asunnot.oikotie.fi/myytavat-asunnot/vantaa/23078097 -o listing.md
        '''
    )
    parser.add_argument('url', help='URL of the real estate listing to scrape')
    parser.add_argument('-o', '--output', help='Output file to save the markdown to')
    
    args = parser.parse_args()
    
    # Create and run the scraper
    scraper = RealEstateScraper(args.url)
    
    if args.output:
        success = scraper.run(args.output)
        if success:
            print(f"Successfully scraped listing and saved to {args.output}")
        else:
            print("Failed to scrape listing")
    else:
        markdown = scraper.run()
        if markdown:
            print(markdown)
        else:
            print("Failed to scrape listing")


if __name__ == '__main__':
    main()
