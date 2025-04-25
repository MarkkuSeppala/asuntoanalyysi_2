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

def get_property_data(markdown_data: str) -> str:
    """
    Hakee kiinteistön perustiedot markdown-muotoisesta datasta käyttäen OpenAI API:a.
    
    Args:
        markdown_data (str): Kiinteistön tiedot markdown-muodossa
        
    Returns:
        str: Kiinteistön perustiedot JSON-merkkijonona tai tyhjä merkkijono, jos haku epäonnistui
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
                            "text": """Tehtävänäsi on poimia syötetystä kiinteistön myynti-ilmoituksesta seuraavat tiedot:

- osoite (katu, kadunnumero ja kaupunki)
- tyyppi (asunnon tyyppi, joka PITÄÄ palauttaa avainsanalla "rakennustyyppi")
- hinta (velaton myyntihinta)
- rakennusvuosi

Rakennustyypin tulee olla jokin seuraavista: "omakotitalo", "kerrostalo", "rivitalo", "erillistalo", "paritalo"
Käytä aina samaa avainta "rakennustyyppi" tyypin määrittämiseen.

Lähetä tieto JSON-muodossa

<esimerkki>
{
  "osoite": {
    "katu": "Esimerkkikatu 1",
    "kaupunki": "Helsinki",
    "postinumero": "00100"
  },
  "rakennustyyppi": "kerrostalo",
  "hinta": "145000",
  "rakennusvuosi": "2005"
}
</esimerkki>

Käytä AINA rakennustyyppi-avainta (ei tyyppi, talotyyppi tai muita variaatioita).
"""
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
        property_data = response.output_text
        logger.info(f"Kiinteistön tiedot haettu onnistuneesti: {property_data}")
        return property_data
        
    except Exception as e:
        logger.error(f"Virhe kiinteistön tietojen hakemisessa: {e}")
        return ""

def save_property_data_to_db(property_data: str, analysis_id: int = None) -> int:
    """
    Tallentaa kiinteistön tiedot tietokantaan
    
    Args:
        property_data (str): Kiinteistön tiedot JSON-merkkijonona
        analysis_id (int, optional): Sen analyysin ID, johon tämä kohde liittyy
        
    Returns:
        int: Luodun kohteen ID tai None, jos tallennus epäonnistui
    """
    try:
        if not property_data:
            logger.error("Kiinteistön tietoja ei voitu tallentaa: Tiedot puuttuvat")
            return None
        
        # Muunnetaan JSON-merkkijono sanakirjaksi
        try:
            data_dict = json.loads(property_data)
            logger.info(f"JSON-merkkijono muunnettu sanakirjaksi onnistuneesti: {data_dict}")
        except json.JSONDecodeError as e:
            logger.error(f"Virhe JSON-merkkijonon muuntamisessa sanakirjaksi: {e}")
            return None
            
        # Muodostetaan osoite yhdeksi kentäksi
        osoite_parts = []
        if "osoite" in data_dict:
            if "katu" in data_dict["osoite"]:
                osoite_parts.append(data_dict["osoite"]["katu"])
            if "kaupunki" in data_dict["osoite"]:
                osoite_parts.append(data_dict["osoite"]["kaupunki"])
        
        osoite = ", ".join(osoite_parts) if osoite_parts else "Tuntematon"
        
        # Muunnetaan hinta numeeriseksi arvoksi
        hinta_str = data_dict.get("hinta", "0")
        try:
            # Poistetaan mahdolliset valuuttamerkit ja välilyönnit
            hinta_str = hinta_str.replace("€", "").replace(" ", "").strip()
            hinta = Decimal(hinta_str)
        except:
            logger.warning(f"Hintaa ei voitu muuntaa numeeriseksi: {hinta_str}")
            hinta = None
        
        # Haetaan rakennustyyppi eri mahdollisista avaimista
        tyyppi = None
        possible_type_keys = ["rakennustyyppi", "tyyppi", "talotyyppi", "asuntotyyppi", "type", "building_type"]
        
        for key in possible_type_keys:
            if key in data_dict and data_dict[key]:
                tyyppi = data_dict[key]
                logger.info(f"Rakennustyyppi löytyi avaimella '{key}': {tyyppi}")
                break
                
        if not tyyppi:
            logger.warning(f"Rakennustyyppiä ei löytynyt JSON-datasta. Saatavilla olevat avaimet: {', '.join(data_dict.keys())}")
        
        # Normalisoidaan rakennustyyppi
        if tyyppi:
            # Muunnetaan kaikki pieniksi kirjaimiksi
            tyyppi = tyyppi.lower()
            
            # Standardoi yleisimmät variaatiot
            type_mapping = {
                'kerrostaloasunto': 'kerrostalo',
                'kerrostalo-osake': 'kerrostalo',
                'kt': 'kerrostalo',
                'kerros': 'kerrostalo',
                'apartment': 'kerrostalo',
                
                'rivitaloasunto': 'rivitalo',
                'rt': 'rivitalo',
                'rivi': 'rivitalo',
                'row house': 'rivitalo',
                
                'omakotitaloasunto': 'omakotitalo',
                'omakotitalo-osake': 'omakotitalo',
                'okt': 'omakotitalo',
                'ok-talo': 'omakotitalo',
                'detached house': 'omakotitalo',
                
                'erillistalo': 'erillistalo',
                'erillinen': 'erillistalo',
                'et': 'erillistalo',
                
                'paritalo': 'paritalo',
                'pt': 'paritalo',
                'semi-detached': 'paritalo'
            }
            
            # Tarkistetaan täsmälliset vastaavuudet
            if tyyppi in type_mapping:
                tyyppi = type_mapping[tyyppi]
            # Tarkistetaan osittaiset vastaavuudet
            else:
                for key, value in type_mapping.items():
                    if key in tyyppi:
                        tyyppi = value
                        break
            
            # Varmistetaan, että tyyppi on joku sallituista arvoista
            valid_types = ['omakotitalo', 'kerrostalo', 'rivitalo', 'erillistalo', 'paritalo']
            if tyyppi not in valid_types:
                logger.warning(f"Tyyppi '{tyyppi}' ei ole sallittu arvo. Käytetään 'tuntematon'.")
                tyyppi = 'tuntematon'
                
            logger.info(f"Lopullinen normalisoitu rakennustyyppi: {tyyppi}")
        
        # Haetaan rakennusvuosi
        rakennusvuosi_str = data_dict.get("rakennusvuosi", None)
        try:
            rakennusvuosi = int(rakennusvuosi_str) if rakennusvuosi_str else None
            if rakennusvuosi:
                logger.info(f"Rakennusvuosi: {rakennusvuosi}")
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
        
        logger.info(f"Luotu kohde: osoite={osoite}, tyyppi={tyyppi}, hinta={hinta}, rakennusvuosi={rakennusvuosi}")
        
        # Lisätään tietokantaan
        db.session.add(kohde)
        db.session.commit()
        
        logger.info(f"Kohde tallennettu tietokantaan ID:llä {kohde.id}")
        return kohde.id
        
    except Exception as e:
        logger.error(f"Virhe kohteen tallentamisessa tietokantaan: {e}")
        logger.error(f"Property data: {property_data}")
        db.session.rollback()
        return None