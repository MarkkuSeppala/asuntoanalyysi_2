from openai import OpenAI
import os
import logging
import json
from models import db, Kohde
from decimal import Decimal

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

# Haetaan OpenAI API-avain ympäristömuuttujasta
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def get_property_data(markdown_data: str) -> dict:
    """
    Hakee kiinteistön perustiedot markdown-muotoisesta datasta käyttäen OpenAI API:a.
    
    Args:
        markdown_data (str): Kiinteistön tiedot markdown-muodossa
        
    Returns:
        dict: Kiinteistön perustiedot sanakirjamuodossa tai tyhjä sanakirja, jos haku epäonnistui
    """
    try:
        logger.info("Haetaan kiinteistön tietoja OpenAI API:sta")
        
        response = client.responses.create(
            model="gpt-4.1-nano",
            input=[
                {
                    "role": "system",
                    "content": [
                        {
                            "type": "input_text",
                            "text": "Tehtävänäsi on poimia syötetystä kiinteistön myynti-ilmoituksesta seuraavat tiedot:\n\n- osoite (katu, kadunnumero ja kaupunki)\n- tyyppi (omakotitalo, kerrostalo, rivitalo, erillistalo, paritalo)\n- hinta (velaton myyntihinta)\n- rakennusvuosi\n\nLähetä tieto JSON-muodossa\n<esimerkki>\n{\n\"osoite\": {\n\"katu\": \"Esimerkkikatu 1\",\n\"kaupunki\": \"Helsinki\",\n\"postinumero\": \"00100\"\n},\n\"rakennustyyppi\": \"kerrostalo\",\n\"hinta\": \"145000\",\n\"rakennusvuosi\": \"2005\"\n}\n</esimerkki>"
                        },
                        {
                            "type": "input_text",
                            "text": markdown_data
                        }
                    ]
                }
            ],
            text={
                "format": {
                    "type": "json_object"
                }
            },
            reasoning={},
            tools=[],
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # Otetaan vastaus JSON-muodossa
        property_data = response.output_json
        logger.info(f"Kiinteistön tiedot haettu onnistuneesti: {property_data}")
        return property_data
        
    except Exception as e:
        logger.error(f"Virhe kiinteistön tietojen hakemisessa: {e}")
        return {}

def save_property_data_to_db(property_data: dict, analysis_id: int = None) -> int:
    """
    Tallentaa kiinteistön tiedot tietokantaan
    
    Args:
        property_data (dict): Kiinteistön tiedot sanakirjamuodossa
        analysis_id (int, optional): Sen analyysin ID, johon tämä kohde liittyy
        
    Returns:
        int: Luodun kohteen ID tai None, jos tallennus epäonnistui
    """
    try:
        if not property_data:
            logger.error("Kiinteistön tietoja ei voitu tallentaa: Tiedot puuttuvat")
            return None
            
        # Muodostetaan osoite yhdeksi kentäksi
        osoite_parts = []
        if "osoite" in property_data:
            if "katu" in property_data["osoite"]:
                osoite_parts.append(property_data["osoite"]["katu"])
            if "kaupunki" in property_data["osoite"]:
                osoite_parts.append(property_data["osoite"]["kaupunki"])
        
        osoite = ", ".join(osoite_parts) if osoite_parts else "Tuntematon"
        
        # Muunnetaan hinta numeeriseksi arvoksi
        hinta_str = property_data.get("hinta", "0")
        try:
            # Poistetaan mahdolliset valuuttamerkit ja välilyönnit
            hinta_str = hinta_str.replace("€", "").replace(" ", "").strip()
            hinta = Decimal(hinta_str)
        except:
            logger.warning(f"Hintaa ei voitu muuntaa numeeriseksi: {hinta_str}")
            hinta = None
        
        # Haetaan rakennustyyppi
        tyyppi = property_data.get("rakennustyyppi", None)
        
        # Haetaan rakennusvuosi
        rakennusvuosi_str = property_data.get("rakennusvuosi", None)
        try:
            rakennusvuosi = int(rakennusvuosi_str) if rakennusvuosi_str else None
        except:
            logger.warning(f"Rakennusvuotta ei voitu muuntaa kokonaisluvuksi: {rakennusvuosi_str}")
            rakennusvuosi = None
        
        # Luodaan uusi kohdeobjekti
        kohde = Kohde(
            osoite=osoite,
            tyyppi=tyyppi,
            hinta=hinta,
            rakennusvuosi=rakennusvuosi,
            analysis_id=analysis_id
        )
        
        # Lisätään tietokantaan
        db.session.add(kohde)
        db.session.commit()
        
        logger.info(f"Kohde tallennettu tietokantaan ID:llä {kohde.id}")
        return kohde.id
        
    except Exception as e:
        logger.error(f"Virhe kohteen tallentamisessa tietokantaan: {e}")
        db.session.rollback()
        return None