from openai import OpenAI
import os
import json
import logging
from models import db, Analysis, RiskAnalysis, Kohde
from flask import current_app
from flask_login import current_user

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Lisätään tiedostolokitus
try:
    # Varmistetaan että logs-hakemisto on olemassa
    os.makedirs('logs', exist_ok=True)
    
    file_handler = logging.FileHandler('logs/riskianalyysi.log')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger = logging.getLogger(__name__)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Varoitus: Lokitiedostoa ei voitu avata: {e}")
    # Jatketaan ilman tiedostolokitusta

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def riskianalyysi(kohde_teksti, analysis_id=None, user_id=None):
    """
    Analysoi asuntokohteen riskitason OpenAI API:n avulla ja tallentaa tuloksen tietokantaan.
    
    Parameters:
    kohde_teksti (str): API-kutsussa tuotettu analyysi kohteesta
    analysis_id (int, optional): Analysis-taulun ID, johon riskianalyysi liitetään
    user_id (int, optional): Käyttäjän ID, jolle riskianalyysi tehdään
    
    Returns:
    str: JSON-muotoinen analyysi riskeistä
    """
    # Tarkistetaan onko kyseessä omakotitalo
    on_omakotitalo = False
    
    try:
        # Tarkistetaan analysis_id:n perusteella kohteen tyyppi
        if analysis_id:
            # Haetaan analyysi
            analyysi = Analysis.query.get(analysis_id)
            if analyysi:
                # Haetaan kohde, joka on linkitetty analyysiin
                kohde = Kohde.query.filter_by(analysis_id=analysis_id).first()
                if kohde and kohde.tyyppi:
                    on_omakotitalo = "omakotitalo" in kohde.tyyppi.lower()
                    logger.info(f"Kohteen tyyppi: {kohde.tyyppi}, omakotitalo: {on_omakotitalo}")
    except Exception as e:
        logger.error(f"Virhe kohteen tyypin tarkistuksessa: {e}")
    
    # Valitaan promptin tiedosto kohteen tyypin mukaan
    prompt_tiedosto = "prompt_riski_okt.txt" if on_omakotitalo else "prompt_riski_kt.txt"
    logger.info(f"Käytetään riskianalyysi-promptia: {prompt_tiedosto}")
    
    try:
        # Lataa promptin tiedostosta
        with open(prompt_tiedosto, "r", encoding="utf-8") as tiedosto:
            prompt = tiedosto.read()
    except Exception as e:
        logger.error(f"Virhe promptin lukemisessa tiedostosta {prompt_tiedosto}: {e}")
        # Käytetään oletuspromptia jos tiedoston lukeminen epäonnistuu
        prompt_tiedosto = "prompt_riski_kt.txt"  # Käytetään oletuksena kerrostalopromptia
        logger.warning(f"Yritetään lukea oletuspromptia: {prompt_tiedosto}")
        
        try:
            with open(prompt_tiedosto, "r", encoding="utf-8") as tiedosto:
                prompt = tiedosto.read()
        except Exception as e:
            logger.error(f"Virhe oletuspromptinkin lukemisessa: {e}")
            # Jos mikään ei toimi, käytetään kovakoodattua promptia
            prompt = """Olet koknut kiinteistöanalyytikko, joka arvioi asuntokohteiden riskejä ostajille. Sinun tehtäväsi on analysoida annettu kohdeanalyysi ja luoda siitä riskianalyysi.

Arvioi kohteen riskitaso analysoimalla oheinen kohteen analyysi. Käytä riskitasoasteikkoa 1-10, jossa 1 on erittäin matala riski ja 10 on erittäin korkea riski.

Analyysi on jaettava eri riskiosa-alueisiin. Arvioi jokaiselle osa-alueelle oma riskitasonsa. Osa-alueet ovat:
1. Sijainti ja alue: Alueen arvonkehitys, maineriski, alueen sosioekonominen status
2. Talous ja rahoitus: Hinnoittelu, arvonkehitys, sijoituksen kannattavuus
3. Kohteen kunto: Rakenteelliset riskit, korjaustarpeet, tekniset järjestelmät
4. Juridiikka: Omistusmuoto, rasitteet, kaavoitus, käyttörajoitukset
5. Taloyhtiö: Jos kyseessä on kerros- tai rivitalo, arvioi taloyhtiön talous, korjausvelka ja hallinnointi

Anna lopuksi kokonaisriskitaso, joka on painotettu keskiarvo osa-alueiden riskeistä.

Vastaa JSON-muodossa:
{
  "kokonaisriskitaso": numero välillä 1-10,
  "riskimittari": [
    {
      "osa_alue": "Sijainti ja alue",
      "riski_taso": numero välillä 1-10,
      "osuus_prosenttia": numero välillä 1-100,
      "kuvaus": "Lyhyt kuvaus riskistä"
    },
    ...seuraaville osa-alueille
  ]
}

Varmista että riskimittarin osa-alueiden osuus_prosenttia-arvojen summa on tasan 100%.
"""
            logger.warning("Käytetään kovakoodattua oletuspromptia.")

    try:
        logger.info("Tehdään riskianalyysi")
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=[
                {
                "role": "system",
                "content": [
                    {
                    "type": "input_text",
                    "text": prompt

                    }
                ]
                },
                {
                "role": "user",
                "content": [
                    {
                    "type": "input_text",
                    "text": kohde_teksti,
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
            temperature=0.9,
            max_output_tokens=2048,
            top_p=0.9,
            store=True
        )
        
        # Tarkistetaan saatu vastaus
        json_text = response.output_text
        logger.info(f"Saatu riskianalyysi: {json_text[:100]}...")
        
        # Varmistetaan että vastaus on validia JSON
        try:
            json_data = json.loads(json_text)
            
            # Validoidaan vastauksen rakenne
            if "kokonaisriskitaso" not in json_data:
                logger.warning("Kokonaisriskitaso puuttuu vastauksesta, lisätään oletusarvo")
                json_data["kokonaisriskitaso"] = 5.0
            else:
                # Pyöristetään kokonaisriskitaso 1 desimaalin tarkkuuteen
                alkuperainen = json_data["kokonaisriskitaso"]
                json_data["kokonaisriskitaso"] = round(float(json_data["kokonaisriskitaso"]), 1)
                logger.info(f"Kokonaisriskitaso: {alkuperainen} -> {json_data['kokonaisriskitaso']}")
                
                # Varmistetaan että kokonaisriskitaso ei ole aina 6.0 testauksen aikana
                
            if "riskimittari" not in json_data or not isinstance(json_data["riskimittari"], list):
                logger.warning("Riskimittari puuttuu tai ei ole listana, korjataan")
                json_data["riskimittari"] = [
                    {
                        "osa_alue": "Kokonaisriski",
                        "riski_taso": json_data.get("kokonaisriskitaso", 5.0),
                        "osuus_prosenttia": 100,
                        "kuvaus": "Arvioitu kokonaisriski kohteelle."
                    }
                ]
                
            # Varmistetaan että jokaisella riskimittarin elementillä on kaikki tarvittavat kentät
            for i, riski in enumerate(json_data["riskimittari"]):
                if "osa_alue" not in riski:
                    riski["osa_alue"] = f"Riski {i+1}"
                if "riski_taso" not in riski:
                    riski["riski_taso"] = 5
                if "osuus_prosenttia" not in riski:
                    # Lasketaan tasainen osuus jokaiselle riskille
                    riski["osuus_prosenttia"] = round(100 / len(json_data["riskimittari"]))
                if "kuvaus" not in riski:
                    riski["kuvaus"] = f"Riskitaso kategorialle {riski['osa_alue']}"
            
            # Muodostetaan JSON-muotoinen tulos
            json_result = json.dumps(json_data, ensure_ascii=False)
            
            # Jos analysis_id on annettu, tallennetaan riskianalyysi tietokantaan
            if analysis_id:
                try:
                    # Tarkistetaan onko tälle analyysille jo olemassa riskianalyysi
                    existing_risk = RiskAnalysis.query.filter_by(analysis_id=analysis_id).first()
                    
                    if existing_risk:
                        # Päivitetään olemassa olevaa riskianalyysiä
                        existing_risk.risk_data = json_result
                        logger.info(f"Päivitettiin riskianalyysi analyysille {analysis_id}")
                    else:
                        # Luodaan uusi riskianalyysi
                        new_risk = RiskAnalysis(
                            analysis_id=analysis_id,
                            risk_data=json_result,
                            user_id=user_id
                        )
                        db.session.add(new_risk)
                        logger.info(f"Luotiin uusi riskianalyysi analyysille {analysis_id}")
                    
                    # Päivitetään kohteen riskitaso
                    try:
                        kohde = Kohde.query.filter_by(analysis_id=analysis_id).first()
                        if kohde:
                            kohde.risk_level = json_data["kokonaisriskitaso"]
                            logger.info(f"Päivitettiin kohteen {kohde.id} riskitaso: {kohde.risk_level}")
                    except Exception as kohde_error:
                        logger.error(f"Virhe tallennettaessa riskitasoa kohteeseen: {kohde_error}")
                    
                    # Tallennetaan muutokset tietokantaan
                    db.session.commit()
                    logger.info("Riskianalyysi tallennettu tietokantaan")
                except Exception as db_error:
                    logger.error(f"Virhe tallennettaessa riskianalyysiä tietokantaan: {db_error}")
                    db.session.rollback()
            
            # Palautetaan korjattu JSON-teksti
            return json_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Vastaus ei ole validia JSON: {e}")
            # Palautetaan virheen sijasta yksinkertainen oletusriski JSON
            default_json = {
                "kokonaisriskitaso": 5.0,
                "riskimittari": [
                    {
                        "osa_alue": "Kokonaisriski",
                        "riski_taso": 5.0,
                        "osuus_prosenttia": 100,
                        "kuvaus": "Kohteen riskitason arviointiin liittyi ongelmia. Tämä on oletusarvio."
                    }
                ]
            }
            return json.dumps(default_json, ensure_ascii=False)
    
    except Exception as e:
        logger.exception(f"Virhe riskianalyysissä: {e}")
        # Palautetaan virheen sijasta yksinkertainen oletusriski JSON
        default_json = {
            "kokonaisriskitaso": 5.0,
            "riskimittari": [
                {
                    "osa_alue": "Kokonaisriski",
                    "riski_taso": 5.0,
                    "osuus_prosenttia": 100,
                    "kuvaus": "Kohteen riskitason arviointiin liittyi virhe. Tämä on oletusarvio."
                }
            ]
        }
        return json.dumps(default_json, ensure_ascii=False)
    