import os
import json
import pdfplumber
import re
import logging
from decimal import Decimal
from models import db, Kohde
import tempfile
import decimal

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("pdf_extract.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 👇 Oletusarvoinen tietojen poimintafunktio (lyhennettynä, olettaa että olet jo määritellyt extract_listing_data)

def extract_listing_data(pdf_path, kaupunki_nimi):
    with pdfplumber.open(pdf_path) as pdf:
        full_text = "\n".join(page.extract_text() or "" for page in pdf.pages)

    data = {}
    
    # Perustiedot
    data["osoite"] = re.search(r"(?:Sijainti|Osoite)\s*[:\-]?\s*([A-ZÅÄÖa-zåäö0-9 ,\-]+?\s+\d+[A-Za-z\-]*[^\n]*)", full_text)
    data["kaupunginosa"] = re.search(r"Kaupunginosa\s+([^\n]+)", full_text)
    data["kaupunki"] = kaupunki_nimi
    data["kohdenumero"] = re.search(r"Kohdenumero\s+([^\n]+)", full_text)
    data["postitoimipaikka"] = re.search(r"Postitoimipaikka\s+([^\n]+)", full_text)
    data["asuinpinta_ala"] = re.search(r"Asuinpinta-ala\s+([0-9,\.]+)\s*m²", full_text)
    data["kokonaispinta_ala"] = re.search(r"Kokonaispinta-ala\s+([0-9,\.]+)\s*m²", full_text)
    data["kerrosala"] = re.search(r"Kerrosala\s+([0-9,\.]+)\s*m²", full_text)
    data["tontin_pinta_ala"] = re.search(r"Tontin pinta-ala\s+([0-9,\.]+)\s*m²", full_text)
    data["muut_tilat"] = re.search(r"Muut tilat\s+([^\n]+)", full_text)
    data["kerros"] = re.search(r"Kerros\s+([^\n]+)", full_text)
    data["kerroksia"] = re.search(r"Kerroksia\s+([^\n]+)", full_text)
    data["huoneiston_kokoonpano"] = re.search(r"Huoneiston kokoonpano\s+([^\n]+)", full_text)
    data["huoneita"] = re.search(r"Huoneita\s+([^\n]+)", full_text)
    data["makuuhuoneita"] = re.search(r"Makuuhuoneita\s+([^\n]+)", full_text)
    data["kunto"] = re.search(r"Kunto\s+([^\n]+)", full_text)
    data["kunnon_lisatiedot"] = re.search(r"Kunnon lisätiedot\s+([^\n]+)", full_text)
    data["vapautuminen"] = re.search(r"Vapautuminen\s+([^\n]+)", full_text)
    data["ensiesittelyssa"] = re.search(r"Ensiesittelyssä\s+([^\n]+)", full_text)
    data["asumistyyppi"] = re.search(r"Asumistyyppi\s+([^\n]+)", full_text)
    data["vuokrattu"] = re.search(r"Vuokrattu\s+([^\n]+)", full_text)
    data["kohdetyyppi"] = re.search(r"Kohde on\s+([^\n]+)", full_text)
    data["uudiskohde"] = re.search(r"Uudiskohde\s+([^\n]+)", full_text)
    data["osakeluettelo_siirretty"] = re.search(r"Osakeluettelo siirretty huoneistojärjestelmään\s+([^\n]+)", full_text)
    data["kiinteistötunnus"] = re.search(r"Kiinteistötunnus\s+([^\n]+)", full_text)
    data["kunnan_numero"] = re.search(r"Kunnan numero\s+([^\n]+)", full_text)

    # Hinta ja rahoitus
    data["velaton_hinta"] = re.search(r"Velaton hinta\s+([0-9\s]+)€", full_text)
    data["myyntihinta"] = re.search(r"Myyntihinta\s+([0-9\s]+)€", full_text)
    data["velkaosuus"] = re.search(r"Velkaosuus\s+([0-9\s]+)€", full_text)
    data["kiinnitykset"] = re.search(r"Kiinnitykset\s+([0-9\s]+)€", full_text)
    data["lainaosuuden_maksu"] = re.search(r"Lainaosuuden maksu\s+([^\n]+)", full_text)
    data["neliöhinta"] = re.search(r"Neliöhinta\s+([0-9\s,]+)\s*/\s*m²", full_text)
    data["yhtiölainoitus"] = re.search(r"Yhtiölainoitus\s+([^\n]+)", full_text)
    data["vastikevastuu_yhtiölainasta"] = re.search(r"Vastikevastuu yhtiölainasta\s+([^\n]+)", full_text)
    data["varainsiirtovero"] = re.search(r"Varainsiirtovero\s+([^\n]+)", full_text)
    data["myydaan_kalustettuna"] = re.search(r"Myydään kalustettuna\s+([^\n]+)", full_text)
    data["muuta_kauppaan_kuuluvaa"] = re.search(r"Muuta kauppaan kuuluvaa\s*:\s*([^\n]+)", full_text)
    match = re.search(r"Rahoitusmuoto\s*((?:.|\n)*?)(?=\n\S|\Z)", full_text, re.DOTALL)
    if match:
        data["rahoitusmuoto"] = match.group(1).strip()

    # Maksut ja vastikkeet
    data["hoitovastike"] = re.search(r"Hoitovastike\s+([^\n€]+)\s*€?\s*/\s*kk", full_text)
    data["pääomavastike"] = re.search(r"Pääomavastike\s+([^\n€]+)\s*€?\s*/\s*kk", full_text)
    data["yhtiövastike_yhteensä"] = re.search(r"Yhtiövastike yhteensä\s+([^\n€]+)\s*€?\s*/\s*kk", full_text)
    data["tontin_vuokravastike"] = re.search(r"Tontin vuokravastike\s+([^\n€]+)\s*€?\s*/\s*kk", full_text)
    data["vesimaksu"] = re.search(r"Vesimaksu\s+([^\n]+)", full_text)
    data["saunan_kustannukset"] = re.search(r"Saunan kustannukset\s+([^\n]+)", full_text)
    data["autopaikan_vuokra"] = re.search(r"(?:Autopaikka|Autopaikan vuokra)\s+([^\n€]+)\s*€?\s*/\s*kk", full_text)
    data["muut_maksut"] = re.search(r"Muut maksut\s+([^\n]+)", full_text)
    data["sähkönkulutus"] = re.search(r"Sähkön.*kulutus.*?([0-9\s]+)\s*kWh(?:/vuosi|/v)?", full_text, re.IGNORECASE)
    data["kiinteistövero"] = re.search(r"Kiinteistövero\s+([^\n€]+)\s*€?\s*/?\s*vuosi?", full_text)

    # Rakennus ja tontti
    data["taloyhtiön_nimi"] = re.search(r"Taloyhtiön nimi\s+([^\n]+)", full_text)
    data["rakennuksen_tyyppi"] = re.search(r"Rakennuksen tyyppi\s+([^\n]+)", full_text)
    data["rakennusvuosi"] = re.search(r"Rakennusvuosi\s+([^\n]+)", full_text)
    data["käyttöönottovuosi"] = re.search(r"Käyttöönottovuosi\s+([^\n]+)", full_text)
    data["rakennusmateriaali"] = re.search(r"Rakennusmateriaali\s+([^\n]+)", full_text)
    data["kattotyyppi"] = re.search(r"Kattotyyppi\s+([^\n]+)", full_text)
    data["kattomateriaali"] = re.search(r"Kattomateriaali\s+([^\n]+)", full_text)
    data["energialuokka"] = re.search(r"Energialuokka\s+([^\n]+)", full_text)
    data["e_luku"] = re.search(r"E-luku\s+([0-9,\.]+)", full_text)
    data["energiatodistus"] = re.search(r"Energiatodistus\s+([^\n]+)", full_text)
    data["rakennusoikeus"] = re.search(r"Rakennusoikeus\s+([0-9,\.]+)\s*m²", full_text)
    data["kaavatilanne"] = re.search(r"Kaavatilanne\s+([^\n]+)", full_text)
    data["kaavoitustiedot"] = re.search(r"Kaavoitustiedot\s+([^\n]+)", full_text)
    data["kaavan_tyyppi"] = re.search(r"Kaavan tyyppi\s+([^\n]+)", full_text)
    data["tontin_omistus"] = re.search(r"Tontin omistus\s+([^\n]+)", full_text)
    data["tontin_koko"] = re.search(r"Tontin koko\s+([0-9,\.]+)\s*m²", full_text)
    data["piha"] = re.search(r"Pihan kuvaus\s+([^\n]+)", full_text)
    data["autopaikat"] = re.search(r"Autopaikat\s+([^\n]+)", full_text)
    data["varasto"] = re.search(r"Varasto\s+([^\n]+)", full_text)
    data["huoneistojen_lukumäärä"] = re.search(r"Huoneistojen lukumäärä\s+([0-9]+)", full_text)

    # Talotekniikka ja lämmitys
    data["lämmitysmuoto"] = re.search(r"Lämmitysmuoto\s+([^\n]+)", full_text)
    data["lämmitysjärjestelmä"] = re.search(r"Lämmitysjärjestelmä\s+([^\n]+)", full_text)
    data["lämmönjakelu"] = re.search(r"Lämmönjako(?:elu)?\s+([^\n]+)", full_text)
    data["ilmalämpöpumppu"] = re.search(r"Ilmalämpöpumppu\s+([^\n]+)", full_text)
    data["varaava_takka"] = re.search(r"Varaava takka\s+([^\n]+)", full_text)
    data["ilmastointi"] = re.search(r"Ilmastointi\s+([^\n]+)", full_text)
    data["ilmanvaihto"] = re.search(r"Ilmanvaihto\s+([^\n]+)", full_text)
    data["antennijärjestelmä"] = re.search(r"Antennijärjestelmä\s+([^\n]+)", full_text)
    data["tietoliikennepalvelut"] = re.search(r"Tietoliikennepalvelut\s+([^\n]+)", full_text)
    data["vesi"] = re.search(r"Vesi(?:johto)?\s*:\s*([^\n]+)", full_text)
    data["viemäröinti"] = re.search(r"Viemäröinti\s*:\s*([^\n]+)", full_text)
    data["kunnallistekniikka"] = re.search(r"Kunnallistekniikka\s+([^\n]+)", full_text)

    # Keittiö
    data["keittiön_varusteet"] = re.search(r"Keittiön varusteet\s+([^\n]+)", full_text)
    data["keittiön_kalusteet"] = re.search(r"Kalusteet\s+([^\n]+)", full_text)
    data["keittiön_työtasot"] = re.search(r"Työtasot\s+([^\n]+)", full_text)
    data["keittiön_lattia"] = re.search(r"Keittiön lattia\s+([^\n]+)", full_text)
    data["keittiön_seinät"] = re.search(r"Keittiön seinät\s+([^\n]+)", full_text)

    # Sauna
    data["kylpyhuoneen_varusteet"] = re.search(r"Kylpyhuone(?:en)? varusteet\s+([^\n]+)", full_text)
    data["wc_varusteet"] = re.search(r"WC(?:-tilojen)? varusteet\s+([^\n]+)", full_text)
    data["sauna"] = re.search(r"Sauna\s+([^\n]+)", full_text)
    data["saunan_varusteet"] = re.search(r"Saunan varusteet\s+([^\n]+)", full_text)

    # MH
    data["makuuhuoneiden_lattia"] = re.search(r"Makuuhuone(?:iden)? lattia\s+([^\n]+)", full_text)
    data["makuuhuoneiden_seinät"] = re.search(r"Makuuhuone(?:iden)? seinät\s+([^\n]+)", full_text)
    data["makuuhuoneiden_varusteet"] = re.search(r"Makuuhuone(?:iden)? varusteet\s+([^\n]+)", full_text)

    # OH
    data["olohuoneen_lattia"] = re.search(r"Olohuone(?:en)? lattia\s+([^\n]+)", full_text)
    data["olohuoneen_seinät"] = re.search(r"Olohuone(?:en)? seinät\s+([^\n]+)", full_text)
    data["olohuoneen_varusteet"] = re.search(r"Olohuone(?:en)? varusteet\s+([^\n]+)", full_text)

    # SÄILYTYS
    data["säilytystilat"] = re.search(r"Säilytystilat\s+([^\n]+)", full_text)
    data["säilytystilojen_varusteet"] = re.search(r"Säilytystilojen varusteet\s+([^\n]+)", full_text)

    # PINTAMATERIAALIT
    data["lattiamateriaalit"] = re.search(r"Lattiamateriaalit\s+([^\n]+)", full_text)
    data["seinämateriaalit"] = re.search(r"Seinämateriaalit\s+([^\n]+)", full_text)
    data["katon_materiaalit"] = re.search(r"Katon materiaalit\s+([^\n]+)", full_text)

    # SIJAINTI JA YMPÄRISTÖ
    data["etäisyys_keskustasta"] = re.search(r"Etäisyys keskustaan\s+([^\n]+)", full_text)
    data["luonnonläheisyys"] = re.search(r"Luonnonläheisyys\s+([^\n]+)", full_text)
    data["palvelut"] = re.search(r"Palvelut\s*[:\-]?\s+([^\n]+)", full_text)
    data["lähin_palvelu"] = re.search(r"Lähin palvelu\s+([^\n]+)", full_text)
    data["koulut"] = re.search(r"Koulut\s+([^\n]+)", full_text)
    data["leikkipuisto_ulkoilualue"] = re.search(r"(Leikkipuisto|Ulkoilualueet?|Puistoalueet?)\s+([^\n]+)", full_text)
    data["veneilymahdollisuus"] = re.search(r"(Venesatama|Veneilymahdollisuus)\s+([^\n]+)", full_text)
    data["liikenneyhteydet"] = re.search(r"Liikenneyhteydet\s+([^\n]+)", full_text)
    data["yhteydet_keskustaan"] = re.search(r"Yhteydet keskustaan\s+([^\n]+)", full_text)

    # ARKKITEHTUURI JA RAKENTAMINEN
    data["arkkitehtisuunnittelu"] = re.search(r"Arkkitehtisuunnittelu\s+([^\n]+)", full_text)
    data["rakennuttaja"] = re.search(r"Rakennuttaja\s+([^\n]+)", full_text)
    data["rakennuskokemus"] = re.search(r"Rakennuskokemus\s+([^\n]+)", full_text)
    data["virtuaaliesittelylinkki"] = re.search(r"(https?://[^\s]+(?:matterport\.com|virtualtour|3d|esittely)[^\s]*)", full_text)

    # REMONTIT
    data["tehdyt_remontit"] = re.search(
        r"Tehdyt remontit[:\s]*\n?((?:.+\n){0,10})", full_text, re.IGNORECASE
    )

    data["tulevat_remontit"] = re.search(
        r"Tulevat remontit(?:\s*\([^)]+\))?[:\s]*\n?((?:.+\n){0,10})", full_text, re.IGNORECASE
    )


    # YHTEISET TILAT
    data["yhteiset_tilat"] = re.search(r"Yhteiset tilat\s+([^\n]+)", full_text)
    data["pysäköintitilan_kuvaus"] = re.search(r"Pysäköintitilan kuvaus\s+([^\n]+)", full_text)

    # ILMOITTAJANTIEDOT
    data["ilmoittajan_nimi"] = re.search(r"(?:Ilmoittaja|Nimi)\s*[:\-]?\s+([^\n]+)", full_text)
    data["ilmoittajan_puhelin"] = re.search(r"(?:Puh\.?|Puhelin)\s*[:\-]?\s+([0-9\s]+)", full_text)
    data["yrityksen_nimi"] = re.search(r"(?:Yritys|Toimisto|Välittäjä)\s*[:\-]?\s+([^\n]+)", full_text)
    data["yrityksen_osoite"] = re.search(r"(?:Yrityksen osoite|Osoite)\s*[:\-]?\s+([^\n]+)", full_text)
    data["yrityksen_puhelin"] = re.search(r"(?:Yrityksen puhelin|Puhelin)\s*[:\-]?\s+([0-9\s]+)", full_text)
    data["toinen_yhteyshenkilö"] = re.search(r"(?:Toinen yhteyshenkilö|Lisätiedot)\s*[:\-]?\s+([^\n]+)", full_text)

    # Puhdistetaan tulokset
    cleaned_data = {}
    for k, v in data.items():
        if isinstance(v, re.Match):
            cleaned_data[k] = v.group(1).strip()
        elif isinstance(v, str):
            cleaned_data[k] = v.strip()
        else:
            cleaned_data[k] = None

    return cleaned_data


# 📁 📄 Käsittele koko kansio

def process_all_pdfs(input_folder, output_json_path, analysis_id=None, user_id=None):
    listings = []

    # 1. Lue olemassa oleva JSON-tiedosto, jos se on olemassa
    if os.path.exists(output_json_path):
        try:
            with open(output_json_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    listings.extend(existing_data)
        except Exception as e:
            logger.error(f"Virhe luettaessa olemassa olevaa JSON-tiedostoa: {e}")

    # 2. Käsittele kaikki PDF-tiedostot pääkansiossa ja alikansioissa
    for root, dirs, files in os.walk(input_folder):
        for filename in files:
            if filename.lower().endswith(".pdf"):
                filepath = os.path.join(root, filename)
                kaupunki_nimi = os.path.basename(root)  # käytä alikansion nimeä "kaupunki"-kenttänä
                logger.info(f"Käsitellään: {filepath} (kaupunki: {kaupunki_nimi})")
                try:
                    extracted = extract_listing_data(filepath, kaupunki_nimi)
                    extracted["tiedostonimi"] = os.path.relpath(filepath, input_folder)
                    extracted["kaupunki"] = kaupunki_nimi  # ylikirjoitetaan mahdollinen vanha arvo
                    listings.append(extracted)
                    
                    # Tallenna tiedot myös tietokantaan
                    kohde_id = save_property_data_to_db(extracted, analysis_id, user_id)
                    if kohde_id:
                        logger.info(f"Tallennettu PDF-tiedot tietokantaan kohde_id: {kohde_id}")
                    else:
                        logger.error(f"Tietokantaan tallentaminen epäonnistui tiedostolle: {filename}")
                        
                except Exception as e:
                    logger.error(f"Virhe tiedostossa {filename}: {e}")

    # 3. Tallenna kaikki tiedot takaisin JSON-tiedostoon
    try:
        with open(output_json_path, "w", encoding="utf-8") as f:
            json.dump(listings, f, indent=2, ensure_ascii=False)
        logger.info(f"Kaikki tiedot tallennettu tiedostoon: {output_json_path}")
        return len(listings)
    except Exception as e:
        logger.error(f"Virhe kirjoitettaessa tiedostoon {output_json_path}: {e}")
        return 0

def process_single_pdf(pdf_path, output_json_path=None, kaupunki_nimi="", analysis_id=None, user_id=None):
    """
    Käsittelee yksittäisen PDF-tiedoston ja tallentaa sen tiedot
    
    Args:
        pdf_path (str): Polku PDF-tiedostoon
        output_json_path (str, optional): Polku JSON-tiedostoon johon tiedot tallennetaan
        kaupunki_nimi (str): Kaupungin nimi
        analysis_id (int, optional): Analyysin ID, johon kohde liittyy
        user_id (int, optional): Käyttäjän ID
        
    Returns:
        dict: Poimitut tiedot sanakirjana ja kohteen ID tietokannassa, tai None jos epäonnistui
    """
    try:
        logger.info(f"Käsitellään yksittäistä PDF-tiedostoa: {pdf_path}")
        extracted = extract_listing_data(pdf_path, kaupunki_nimi)
        extracted["tiedostonimi"] = os.path.basename(pdf_path)
        
        # Tallenna tietokantaan
        kohde_id = save_property_data_to_db(extracted, analysis_id, user_id)
        extracted["kohde_id"] = kohde_id
        
        # Tallenna JSON-tiedostoon jos polku on annettu
        if output_json_path:
            listings = []
            if os.path.exists(output_json_path):
                try:
                    with open(output_json_path, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                        if isinstance(existing_data, list):
                            listings.extend(existing_data)
                except Exception as e:
                    logger.error(f"Virhe luettaessa olemassa olevaa JSON-tiedostoa: {e}")
            
            listings.append(extracted)
            
            try:
                with open(output_json_path, "w", encoding="utf-8") as f:
                    json.dump(listings, f, indent=2, ensure_ascii=False)
                logger.info(f"Tiedot tallennettu tiedostoon: {output_json_path}")
            except Exception as e:
                logger.error(f"Virhe kirjoitettaessa tiedostoon {output_json_path}: {e}")
        
        return extracted
        
    except Exception as e:
        logger.error(f"Virhe käsiteltäessä tiedostoa {pdf_path}: {e}")
        return None


def save_property_data_to_db(extracted_data, analysis_id=None, user_id=None):
    """
    Tallentaa PDF:stä poimitut kiinteistön tiedot tietokantaan
    
    Args:
        extracted_data (dict): PDF:stä poimitut tiedot sanakirjana
        analysis_id (int, optional): Analyysin ID, johon kohde liittyy
        user_id (int, optional): Käyttäjän ID
        
    Returns:
        int: Luodun kohteen ID tai None, jos tallennus epäonnistui
    """
    try:
        if not extracted_data:
            logger.error("Kiinteistön tietoja ei voitu tallentaa: Tiedot puuttuvat")
            return None
        
        # Haetaan tarvittavat tiedot
        osoite = None
        # Tarkistetaan onko osoite sanakirjana vai merkkijonona
        if isinstance(extracted_data.get("osoite"), dict):
            # Muodostetaan osoite merkkijonoksi
            osoite_dict = extracted_data.get("osoite")
            osoite_parts = []
            if "katu" in osoite_dict and osoite_dict["katu"]:
                osoite_parts.append(osoite_dict["katu"])
            if "kaupunki" in osoite_dict and osoite_dict["kaupunki"]:
                osoite_parts.append(osoite_dict["kaupunki"])
            
            osoite = ", ".join(osoite_parts) if osoite_parts else "Tuntematon"
            logger.info(f"Muodostettu osoite sanakirjasta: '{osoite}'")
        else:
            osoite = extracted_data.get("osoite") or "Tuntematon"
        
        # Haetaan rakennustyyppi
        tyyppi = None
        # Tarkistetaan eri rakennustyyppi-kentät
        if "rakennustyyppi" in extracted_data:
            tyyppi = extracted_data.get("rakennustyyppi")
        elif "rakennuksen_tyyppi" in extracted_data:
            tyyppi = extracted_data.get("rakennuksen_tyyppi")
        
        # Käsitellään hinta (ensisijaisesti velaton hinta, toissijaisesti myyntihinta)
        hinta_str = None
        if extracted_data.get("velaton_hinta"):
            hinta_str = extracted_data.get("velaton_hinta")
        elif extracted_data.get("myyntihinta"):
            hinta_str = extracted_data.get("myyntihinta")
        elif extracted_data.get("hinta"):
            hinta_str = extracted_data.get("hinta")
            
        hinta = None
        if hinta_str:
            try:
                # Convert to string and remove currency symbols
                hinta_str = str(hinta_str).replace("€", "").strip()
                
                # DEBUG: Log the raw price string
                logger.info(f"Raw price string: '{hinta_str}'")
                
                # IMPORTANT: Remove ALL spaces first - this is critical for formats like "339 000"
                hinta_str = ''.join(hinta_str.split())
                
                # DEBUG: Log the cleaned price string
                logger.info(f"Cleaned price string: '{hinta_str}'")
                
                # Replace comma with dot for decimal handling
                hinta_str = hinta_str.replace(",", ".")
                
                # If we have multiple dots (e.g., European format like 1.234.567,89)
                if hinta_str.count(".") > 1:
                    parts = hinta_str.split(".")
                    hinta_str = "".join(parts[:-1]) + "." + parts[-1]
                
                # If string is empty after cleaning, skip conversion
                if not hinta_str:
                    logger.warning("Empty price string after cleaning")
                    hinta = None
                else:
                    # Try direct integer conversion as a fallback
                    try:
                        hinta = Decimal(hinta_str)
                        logger.info(f"Successfully converted price: {hinta}")
                    except:
                        # For pure integer values, extra safety
                        hinta = Decimal(int(float(hinta_str)))
                        logger.info(f"Converted price using fallback: {hinta}")
            except Exception as e:
                logger.warning(f"Hintaa ei voitu muuntaa numeeriseksi: '{hinta_str}': {str(e)} ({type(e).__name__})")
                hinta = None
                
        # Poimitaan rakennusvuosi
        rakennusvuosi = None
        if extracted_data.get("rakennusvuosi"):
            try:
                rakennusvuosi = int(extracted_data.get("rakennusvuosi"))
            except Exception as e:
                logger.warning(f"Rakennusvuotta ei voitu muuntaa kokonaisluvuksi: {extracted_data.get('rakennusvuosi')}: {str(e)}")
                
        # Poimitaan pinta-ala
        neliot = None
        if extracted_data.get("asuinpinta_ala"):
            try:
                neliot_str = extracted_data.get("asuinpinta_ala").replace(",", ".").replace(" ", "")
                neliot = float(neliot_str)
            except Exception as e:
                logger.warning(f"Pinta-alaa ei voitu muuntaa numeroksi: {extracted_data.get('asuinpinta_ala')}: {str(e)}")
                
        # Poimitaan huoneiden lukumäärä
        huoneet = None
        if extracted_data.get("huoneita"):
            try:
                huoneet = int(extracted_data.get("huoneita"))
            except Exception as e:
                logger.warning(f"Huoneiden lukumäärää ei voitu muuntaa kokonaisluvuksi: {extracted_data.get('huoneita')}: {str(e)}")
        
        # Luodaan uusi kohdeobjekti
        kohde = Kohde(
            osoite=osoite,
            tyyppi=tyyppi,
            hinta=hinta,
            rakennusvuosi=rakennusvuosi,
            analysis_id=analysis_id,
            user_id=user_id,
            neliot=neliot,
            huoneet=huoneet
        )
        
        logger.info(f"Luotu kohde: osoite={osoite}, tyyppi={tyyppi}, hinta={hinta}, rakennusvuosi={rakennusvuosi}, neliot={neliot}, huoneet={huoneet}")
        
        # Lisätään tietokantaan
        db.session.add(kohde)
        db.session.commit()
        
        logger.info(f"Kohde tallennettu tietokantaan ID:llä {kohde.id}")
        return kohde.id
        
    except Exception as e:
        logger.error(f"Virhe kohteen tallentamisessa tietokantaan: {e}")
        db.session.rollback()
        return None

def get_property_data(markdown_data: str) -> str:
    """
    Compatibility function to replace kat_api_call.get_property_data
    
    Args:
        markdown_data (str): Property data in markdown format
        
    Returns:
        str: Property data in JSON format, or empty string if extraction failed
    """
    try:
        logger.info("Käytetään info_extract.get_property_data funktioita")
        
        # Create a temporary file from the markdown data
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as temp:
            temp_path = temp.name
            temp.write(markdown_data.encode('utf-8'))
        
        # Convert the markdown to PDF format first (requires additional implementation)
        # For now, we'll extract what we can from the markdown directly
        extracted_data = {}
        
        # Extract key information using regular expressions
        osoite_match = re.search(r"(?:Sijainti|Osoite)[:\s]*([^\n]+)", markdown_data)
        if osoite_match:
            osoite = osoite_match.group(1).strip()
            extracted_data["osoite"] = osoite
            
            # Try to split address into parts
            osoite_parts = osoite.split(',')
            if len(osoite_parts) >= 2:
                katu = osoite_parts[0].strip()
                kaupunki = osoite_parts[-1].strip()
                extracted_data["osoite_katu"] = katu
                extracted_data["osoite_kaupunki"] = kaupunki
        
        # Extract property type
        tyyppi_match = re.search(r"(?:Tyyppi|Talotyyppi|Rakennuksen tyyppi)[:\s]*([^\n]+)", markdown_data)
        if tyyppi_match:
            tyyppi = tyyppi_match.group(1).strip().lower()
            # Map to standard types
            if 'kerrostalo' in tyyppi or 'kt' in tyyppi:
                extracted_data["rakennustyyppi"] = "kerrostalo"
            elif 'rivitalo' in tyyppi or 'rt' in tyyppi:
                extracted_data["rakennustyyppi"] = "rivitalo"
            elif 'omakotitalo' in tyyppi or 'okt' in tyyppi:
                extracted_data["rakennustyyppi"] = "omakotitalo"
            elif 'paritalo' in tyyppi or 'pt' in tyyppi:
                extracted_data["rakennustyyppi"] = "paritalo"
            elif 'erillistalo' in tyyppi:
                extracted_data["rakennustyyppi"] = "erillistalo"
            else:
                extracted_data["rakennustyyppi"] = "tuntematon"
        
        # Extract price
        hinta_match = re.search(r"(?:Velaton hinta|Myyntihinta|Hinta)[:\s]*([0-9\s]+)(?:€|\s*eur)", markdown_data, re.IGNORECASE)
        if hinta_match:
            hinta = hinta_match.group(1).strip().replace(" ", "")
            extracted_data["hinta"] = hinta
            
        # Extract construction year
        vuosi_match = re.search(r"(?:Rakennusvuosi)[:\s]*([0-9]{4})", markdown_data)
        if vuosi_match:
            rakennusvuosi = vuosi_match.group(1).strip()
            extracted_data["rakennusvuosi"] = rakennusvuosi
            
        # Extract square meters (neliot)
        neliot_match = re.search(r"(?:Asuinpinta-ala|Pinta-ala|Kokonaispinta-ala|Neliöt)[:\s]*([0-9,\.]+)\s*(?:m²|m2)", markdown_data, re.IGNORECASE)
        if neliot_match:
            neliot = neliot_match.group(1).strip().replace(",", ".")
            extracted_data["asuinpinta_ala"] = neliot
            logger.info(f"Löydettiin pinta-ala: {neliot} m²")
            
        # Extract room count (huoneet)
        huoneet_match = re.search(r"(?:Huoneet|Huoneita|Huoneluku)[:\s]*([0-9]+)", markdown_data, re.IGNORECASE)
        if not huoneet_match:
            # Try alternative: Look for "4h+k" type pattern
            huoneet_match = re.search(r"(\d+)\s*h(?:\+[kKtT])?", markdown_data)
        
        if huoneet_match:
            huoneet = huoneet_match.group(1).strip()
            extracted_data["huoneita"] = huoneet
            logger.info(f"Löydettiin huoneita: {huoneet}")

        # Format as JSON for compatibility
        formatted_data = {
            "osoite": {
                "katu": extracted_data.get("osoite_katu", ""),
                "kaupunki": extracted_data.get("osoite_kaupunki", "")
            },
            "rakennuksen_tyyppi": extracted_data.get("rakennustyyppi", "tuntematon"),
            "hinta": extracted_data.get("hinta", ""),
            "rakennusvuosi": extracted_data.get("rakennusvuosi", ""),
            "asuinpinta_ala": extracted_data.get("asuinpinta_ala", ""),
            "huoneita": extracted_data.get("huoneita", "")
        }
        
        # Convert to JSON string
        return json.dumps(formatted_data, ensure_ascii=False)
        
    except Exception as e:
        logger.error(f"Virhe get_property_data-funktiossa: {e}")
        return ""

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Käsitellään yksittäinen PDF-tiedosto
        pdf_path = sys.argv[1]
        output_json = "oikotie.json" if len(sys.argv) <= 2 else sys.argv[2]
        kaupunki = "Tuntematon" if len(sys.argv) <= 3 else sys.argv[3]
        
        logger.info(f"Käsitellään yksittäinen tiedosto: {pdf_path}")
        result = process_single_pdf(pdf_path, output_json, kaupunki)
        if result and result.get("kohde_id"):
            print(f"\n✅ Tiedot tallennettu tietokantaan (kohde_id: {result.get('kohde_id')}) ja tiedostoon: {output_json}")
        else:
            print("\n❌ Virhe PDF-tiedoston käsittelyssä.")
    else:
        # Käsitellään koko kansio
        kansio = "D:/OIKOTIE LATAUKSET/testi"  # pääkansio, jossa alikansioita
        json_output = "oikotie.json"
        count = process_all_pdfs(kansio, json_output)
        print(f"\n✅ Valmis! Käsitelty {count} PDF-tiedostoa. Tiedot tallennettu tiedostoon: {json_output}")

