from openai import OpenAI
import logging
import os
import time
import json
import requests
import re
from typing import Optional, Dict, Any
from datetime import datetime
import hashlib
from models import db, Analysis, RiskAnalysis
from flask_login import current_user

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

# Hakemisto, johon analyysit tallennetaan
ANALYSES_DIR = "analyses"
os.makedirs(ANALYSES_DIR, exist_ok=True)  # Varmistetaan että hakemisto on olemassa

# Haetaan OpenAI API-avain ympäristömuuttujasta tai käytä oletusarvoa
api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# Vakiovastaukset virhetilanteisiin
ERROR_MESSAGES = {
    "general": "Analyysin hakeminen epäonnistui. Yritä uudelleen myöhemmin.",
    "api_error": "OpenAI API-virhe. Palvelu voi olla tilapäisesti poissa käytöstä.",
    "rate_limit": "Liian monta pyyntöä lyhyessä ajassa. Odota hetki ja yritä uudelleen.",
    "timeout": "Pyyntö aikakatkaistiin. Verkkoyhteydessä voi olla ongelmia.",
    "auth_error": "Tunnistautumisvirhe. Tarkista API-avain.",
    "invalid_request": "Virheellinen pyyntö. Tarkista syötetyt tiedot."
}

def sanitize_markdown_response(text: str) -> str:
    """
    Poistaa API-vastauksesta markdown-sanat, jotka voivat sekoittaa koodin myöhemmin.
    
    Args:
        text (str): API-vastaus, joka voi sisältää markdown-sanoja
        
    Returns:
        str: Puhdistettu vastaus ilman markdown-sanoja
    """
    if not text:
        return text
        
    # Poista mahdolliset "```markdown" ja "```" -merkinnät
    text = re.sub(r'^```markdown\s*', '', text)
    text = re.sub(r'\s*```$', '', text)
    
    # Poista muut mahdolliset koodiblokki-merkinnät
    text = re.sub(r'^```\w*\s*', '', text)
    
    # Poista "Vastaus markdown-muodossa:" tyyppiset alut
    text = re.sub(r'^.*[vV]astaus [mM]arkdown[ -][mM]uodossa:?\s*', '', text)
    text = re.sub(r'^.*MARKDOWN[ -]MUODOSSA:?\s*', '', text)
    
    # Poista "Tässä analyysi markdown-muodossa:" tyyppiset alut
    text = re.sub(r'^.*[aA]nalyysi [mM]arkdown[ -][mM]uodossa:?\s*', '', text)
    
    # Poista "Oheinen vastaus on markdown-muodossa:" tyyppiset alut
    text = re.sub(r'^.*on [mM]arkdown[ -][mM]uodossa:?\s*', '', text)
    
    # Poista "Markdown:" tyyppiset alut
    text = re.sub(r'^.*[mM]arkdown:?\s*', '', text)
    
    # Poista vastauksen lopussa mahdollisesti olevat markdown-viittaukset
    text = re.sub(r'\s*\(markdown[ -]muodossa\)\s*$', '', text)
    text = re.sub(r'\s*\[markdown\]\s*$', '', text)
    
    # Korvaa mahdolliset useammat peräkkäiset tyhjät rivit yhdellä
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    logger.debug("Sanitoitu markdown-vastaus")
    return text.strip()

def get_analysis(markdown_data: str, property_url: str = None) -> str:
    """
    Lähettää asunnon tiedot markdown-muodossa OpenAI:lle ja pyytää analyysin.
    
    Args:
        markdown_data (str): Asunnon tiedot markdown-muodossa
        property_url (str, optional): Analysoitavan asunnon URL
        
    Returns:
        str: OpenAI:n tuottama analyysi
    """
    if not markdown_data:
        logger.error("Markdown-data puuttuu")
        return ERROR_MESSAGES["invalid_request"]
    
    retry_count = 0
    max_retries = 3
    backoff_time = 2  # sekunteina
    
    while retry_count < max_retries:
        try:
            logger.info(f"Lähetetään analyysiä OpenAI API:lle (yritys {retry_count + 1}/{max_retries})")
            logger.debug(f"Markdown datan pituus: {len(markdown_data)} merkkiä")
            
            # Sama system-ohje kuin alkuperäisessä koodissa
            system_prompt = """Olet kiinteistö- ja kiinteistövälityksen kokenut ammattilainen.
Tehtävänäsi on tehdä ostajalle analyysi myynnisssä olevasta kohteesta.

**TÄMÄ ON TÄRKEÄÄ:**
Perhedy tietoihin huolellisesi. Tee kohteen tiedoista implisiittisiä päätelmiä ostajalle tärkeistä asioista.

Analyysin alussa on yhteenveto. Tee siitä hyvin napakka ja jopa räväkkä. On tärkeää, että kiinnittää huomiota.
Kerro suorasanaisesti kohteen puutteet ja vahvuudet. Vältä toistoa.

Laadi teksi asiantuntijamaiseen tyyliin. Kerro kuitenkin suoraan kohteen puutteet ja negatiiviset asiat.
Vältä ilmoitustekstin toistoa, ilman että siinä on mielestäsi jotain huomioitavaa. Ota huomioon, että lukija on jo perehtynyt ilmoituksen sisältöön ja odottaa nyt sinulta huomioita, jotka eivät suoraan ilmene tekstistä.
Koosta analyysin loppuun kolmen kysymyksen kysymyslista. Tee sellaisia kysymyksiä, jotka ovat oikeasti merkittäviä ostajalle.
Älä kommentoi välitysliikettä tai välittäjää.

Alla kuvaus vastauksen rakenteesta.

<rakennekuvaus>
**KOHDE:**
\"Kaivokselantie 5, Vantaa\"

<yhteenveto>
*Hinta:* (kerro pyyntihinta ja esitä tässä myös oma hinta-arviosi, mutta huomioi, että ostajat olettavat saavansa aina ostotilanteessa noin 5% alennuksen.)
*Sijainti:*
*Taloyhtiö ja rakennus:*
</yhteenveto>

*1. Sijainti ja alueellinen konteksti*
Anna tässä rehellinen kuvaus alueesta, jossa kiinteistö sijaitsee. Kerro suoraan, jos alue on maineeltaan kyseenalainen.

*2. Rakennus ja taloyhtiö*
Pyri tekemään omia päätelmiäsi siitä, millainen rakennus ja taloyhtiö on kyseessä, myös sen perusteella, mitä ilmoituksessa ei ole sanottu. On tärkeää, ettei tässä kohdassa ainoastaan toisteta samoja asioita, jotka ilmenevät jo ilmoituksessa.

*3. Asunto ja varustelutaso*
*4. Markkina- ja ostotilanne*
*5. Mahdolliset huomiot tai riskitekijät*
Tämä on tärkeä osio. Pyri kirjoittamaan tämä osio mahdollisimman vakuuttavasti, niin että lukija kokee saaneensa arvokasta tietoa.

*6. Kohteen hinta verrattuna vastaaviin*
Anna tässä konkreettinen oma hinta-arviosi kohteesta perusteluineen.

*7. Kysymyslista välittäjälle*
Listaa tähän kolme kysymystä, jotka olisi mielestäsi tärkeä kysyä välittäjältä.
</rakennekuvaus>

HUOM! Analysoitava ilmoitus saattaa sisältää ilmoitukseen liittymätöntä mainosmateriaalia. Jos havaitset tällaista, älä käytä sitä analyysissa.


**Tämä on tärkeää:** ANNA VASTAUS MARKDOWN -MUODOSSA!"""

            start_time = time.time()
            
            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "system",
                        "content": [
                            {
                                "type": "input_text",
                                "text": system_prompt
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
                        "type": "text"
                    }
                },
                reasoning={},
                tools=[],
                temperature=1,
                max_output_tokens=2048,
                top_p=1,
                store=True
            )
            
            elapsed_time = time.time() - start_time
            logger.info(f"OpenAI API vastasi ajassa {elapsed_time:.2f} sekuntia")
            
            if hasattr(response, 'output_text') and response.output_text:
                logger.info("Analyysi haettu onnistuneesti")
                # Lokitetaan vain osa vastauksesta yksityisyyssyistä
                content_preview = response.output_text[:100] + "..." if len(response.output_text) > 100 else response.output_text
                logger.debug(f"Vastauksen alku: {content_preview}")
                
                # Sanitoidaan vastaus ennen tallennusta ja palautusta
                sanitized_response = sanitize_markdown_response(response.output_text)
                
                # Tallennetaan analyysi tiedostoon ja tietokantaan
                saved_file = save_analysis_to_file(sanitized_response, markdown_data, property_url)
                
                return sanitized_response
            else:
                logger.error("OpenAI API ei palauttanut odotettua vastausta")
                return ERROR_MESSAGES["general"]
                
        except requests.exceptions.Timeout:
            logger.warning(f"Pyyntö aikakatkaistiin (yritys {retry_count + 1}/{max_retries})")
            if retry_count == max_retries - 1:
                return ERROR_MESSAGES["timeout"]
                
        except requests.exceptions.ConnectionError:
            logger.error(f"Yhteysvirhe (yritys {retry_count + 1}/{max_retries})")
            if retry_count == max_retries - 1:
                return ERROR_MESSAGES["general"]
                
        except requests.exceptions.HTTPError as http_err:
            status_code = getattr(http_err.response, 'status_code', None)
            
            if status_code == 401:
                logger.error("Tunnistautumisvirhe: Virheellinen API-avain")
                return ERROR_MESSAGES["auth_error"]
            elif status_code == 429:
                logger.warning(f"Liian monta pyyntöä - rajaa rajoitettu (yritys {retry_count + 1}/{max_retries})")
                # Odota pidempään rate limit -virheissä
                time.sleep(backoff_time * 2)
                backoff_time *= 2
                retry_count += 1
                continue
            else:
                logger.error(f"HTTP-virhe: {http_err}")
                return ERROR_MESSAGES["api_error"]
                
        except json.JSONDecodeError:
            logger.error("Virheellinen JSON-vastaus OpenAI API:lta")
            return ERROR_MESSAGES["api_error"]
            
        except Exception as e:
            logger.exception(f"Odottamaton virhe: {str(e)}")
            return ERROR_MESSAGES["general"]
            
        # Eksponentiaalinen backoff uudelleenyritysten välillä
        time.sleep(backoff_time)
        backoff_time *= 2
        retry_count += 1
        
    # Jos kaikki yritykset epäonnistuvat
    logger.error(f"Kaikki {max_retries} yritystä epäonnistuivat")
    return ERROR_MESSAGES["general"]

def save_analysis_to_file(analysis: str, markdown_data: str, property_url: str = None) -> str:
    """
    Tallentaa analyysin tekstitiedostoon analyses-hakemistoon ja tietokantaan.
    
    Args:
        analysis (str): Analyysi teksti
        markdown_data (str): Alkuperäinen markdown-muotoinen data, josta analyysi tehtiin
        property_url (str, optional): Analysoitavan asunnon URL
        
    Returns:
        str: Tallennetun tiedoston polku
    """
    try:
        # Luodaan yksilöllinen tiedostonimi aikaleiman ja datan tiivisteen avulla
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Luodaan tiiviste datan alusta tunnistamista varten
        data_preview = markdown_data[:100] if markdown_data else ""
        hash_digest = hashlib.md5(data_preview.encode('utf-8')).hexdigest()[:8]
        
        # Luodaan tiedoston nimi
        filename = f"analyysi_{timestamp}_{hash_digest}.txt"
        filepath = os.path.join(ANALYSES_DIR, filename)
        
        # Etsitään osoitetta tai otsikkoa markdown-datasta
        address_or_title = ""
        for line in markdown_data.split("\n"):
            if line.startswith("# "):  # Markdown-otsikko
                address_or_title = line[2:].strip()
                break
        
        # Tallennetaan analyysi tiedostoon
        with open(filepath, "w", encoding="utf-8") as file:
            # Kirjoitetaan otsikko ja aikaleima
            file.write(f"# Asuntoanalyysi {timestamp}\n\n")
            
            if address_or_title:
                file.write(f"Kohde: {address_or_title}\n\n")
                
            # Kirjoitetaan varsinainen analyysi
            file.write("## ANALYYSI\n\n")
            file.write(analysis)
            
            # Lisätään alaviite
            file.write(f"\n\n---\nGeneroitu {datetime.now().strftime('%d.%m.%Y klo %H:%M:%S')}\n")
        
        # Tallennetaan analyysi tietokantaan, jos käyttäjä on kirjautunut
        if current_user and current_user.is_authenticated:
            try:
                # Luodaan uusi analyysi
                db_analysis = Analysis(
                    filename=filename,
                    title=address_or_title or f"Analyysi {timestamp}",
                    property_url=property_url,
                    content=analysis,
                    user_id=current_user.id
                )
                
                # Lisätään tietokantaan
                db.session.add(db_analysis)
                db.session.commit()
                
                logger.info(f"Analyysi tallennettu tietokantaan käyttäjälle {current_user.username}")
            except Exception as db_err:
                logger.error(f"Virhe analyysin tallentamisessa tietokantaan: {db_err}")
                # Jatketaan, vaikka tietokantaan tallennus epäonnistuisi
        
        logger.info(f"Analyysi tallennettu tiedostoon: {filepath}")
        return filepath
        
    except Exception as e:
        logger.error(f"Virhe analyysin tallentamisessa tiedostoon: {e}")
        return ""

def log_request_details(data: Dict[str, Any]) -> None:
    """
    Lokittaa tietoja API-pyynnöstä ilman arkaluontoisia tietoja.
    
    Args:
        data: Pyyntötiedot
    """
    try:
        # Poista tai maskaa arkaluontoiset tiedot
        safe_data = {k: v for k, v in data.items() if k not in ['api_key']}
        if 'markdown_data' in safe_data:
            safe_data['markdown_data_length'] = len(safe_data['markdown_data'])
            del safe_data['markdown_data']
            
        logger.debug(f"Pyyntötiedot: {json.dumps(safe_data)}")
    except Exception as e:
        logger.warning(f"Pyyntötietojen lokitus epäonnistui: {e}")

def get_saved_analyses(user_id=None) -> list:
    """
    Palauttaa listan tallennetuista analyyseistä.
    
    Args:
        user_id (int, optional): Käyttäjän ID, jonka analyysit haetaan
        
    Returns:
        list: Lista tiedostopolkuja tallennetuista analyyseistä
    """
    try:
        if user_id:
            # Jos käyttäjä annettu, haetaan vain kyseisen käyttäjän analyysit
            from models import Analysis
            return Analysis.query.filter_by(user_id=user_id).order_by(Analysis.created_at.desc()).all()
        
        # Muuten haetaan kaikki analyysit tiedostojärjestelmästä
        if not os.path.exists(ANALYSES_DIR):
            logger.warning(f"Analyses-hakemistoa ei löydy: {ANALYSES_DIR}")
            return []
            
        files = [os.path.join(ANALYSES_DIR, f) for f in os.listdir(ANALYSES_DIR) 
                if f.startswith("analyysi_") and f.endswith(".txt")]
        
        # Järjestetään uusimmat ensin
        files.sort(key=os.path.getmtime, reverse=True)
        
        return files
    except Exception as e:
        logger.error(f"Virhe tallennettujen analyysien listaamisessa: {e}")
        return []