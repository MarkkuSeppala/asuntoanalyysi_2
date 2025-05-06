"""
Asuntotietojen poimintamoduuli

Tämä moduuli tarjoaa funktioita asuntotietojen poimintaan tekstitiedostoista ja PDF-tiedostoista.
Se toimii siltana kat_api_call.py ja sovelluksen välillä, tarjoten yhtenäisen rajapinnan.
"""

import os
import logging
import json
import tempfile
from kat_api_call import get_property_data as kat_get_property_data
from kat_api_call import save_property_data_to_db as kat_save_property_data
import oikotie_downloader
import etuovi_downloader

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("api_calls.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_property_data(markdown_data: str) -> str:
    """
    Hakee kiinteistön perustiedot markdown-muotoisesta datasta käyttäen kat_api_call moduulia.
    
    Args:
        markdown_data (str): Kiinteistön tiedot markdown-muodossa
        
    Returns:
        str: Kiinteistön perustiedot JSON-merkkijonona tai tyhjä merkkijono, jos haku epäonnistui
    """
    try:
        logger.info("Kutsutaan kat_api_call.get_property_data")
        return kat_get_property_data(markdown_data)
    except Exception as e:
        logger.error(f"Virhe kiinteistön tietojen hakemisessa: {e}")
        return ""

def save_property_data_to_db(property_data, analysis_id=None, user_id=None):
    """
    Tallentaa kiinteistön tiedot tietokantaan käyttäen kat_api_call moduulia.
    
    Args:
        property_data: Kiinteistön tiedot dictionary- tai JSON-merkkijono-muodossa
        analysis_id (int, optional): Analyysin ID, johon kohde liittyy
        user_id (int, optional): Käyttäjän ID, jolle kohde kuuluu
    
    Returns:
        int: Luodun kohteen ID tai None, jos tallennus epäonnistui
    """
    try:
        logger.info("Kutsutaan kat_api_call.save_property_data_to_db")
        # Jos property_data on dictionary, muunnetaan se JSON-merkkijonoksi
        if isinstance(property_data, dict):
            property_data = json.dumps(property_data)
        
        return kat_save_property_data(property_data, analysis_id, user_id)
    except Exception as e:
        logger.error(f"Virhe kiinteistön tietojen tallentamisessa: {e}")
        return None

def process_single_pdf(pdf_path, kaupunki_nimi="PDF-lataus", user_id=None):
    """
    Käsittelee yksittäisen PDF-tiedoston ja palauttaa siitä poimitut tiedot.
    
    Args:
        pdf_path (str): Polku PDF-tiedostoon
        kaupunki_nimi (str): Kaupungin nimi, jos tiedossa (oletuksena "PDF-lataus")
        user_id (int): Käyttäjän ID, jolle tiedot tallennetaan
    
    Returns:
        dict: Poimitut tiedot tai None, jos poiminta epäonnistui
    """
    try:
        logger.info(f"Käsitellään PDF-tiedosto: {pdf_path}")
        
        # Poimitaan teksti PDF-tiedostosta
        text_content = oikotie_downloader.extract_text_from_pdf(pdf_path)
        
        if not text_content:
            logger.error("PDF-tiedostosta ei saatu tekstiä")
            return None
        
        # Luodaan väliaikainen tiedostonimi PDF:n polusta
        import os
        import time
        file_stem = os.path.splitext(os.path.basename(pdf_path))[0]
        property_id = f"{file_stem}_{int(time.time())}"
        
        # Muotoillaan teksti markdown-muotoon analyysiä varten
        markdown_data = f"""# PDF-asuntoilmoitus

## Perustiedot
Lähde: Ladattu PDF
Tiedostonimi: {os.path.basename(pdf_path)}
ID: {property_id}
Sijainti: {kaupunki_nimi}

## Ilmoituksen sisältö
{text_content}
"""
        
        # Haetaan perustiedot OpenAI API:lla
        property_data_json = get_property_data(markdown_data)
        
        if not property_data_json:
            logger.error("Perustietojen poiminta PDF:stä epäonnistui")
            return None
        
        try:
            property_data = json.loads(property_data_json)
            
            # Tallennetaan tiedot tietokantaan
            kohde_id = save_property_data_to_db(property_data, user_id=user_id)
            
            if kohde_id:
                logger.info(f"PDF:stä poimitut tiedot tallennettiin kohteeseen ID {kohde_id}")
                property_data["kohde_id"] = kohde_id
            
            return property_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Virhe JSON-datan käsittelyssä: {e}")
            return None
            
    except Exception as e:
        logger.error(f"Virhe PDF:n käsittelyssä: {e}")
        return None 