from openai import OpenAI
import os
import json
import logging
from models import db, Analysis, RiskAnalysis
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


def riskianalyysi(kohde_teksti, analysis_id=None):
    """
    Analysoi asuntokohteen riskitason OpenAI API:n avulla ja tallentaa tuloksen tietokantaan.
    
    Parameters:
    kohde_teksti (str): API-kutsussa tuotettu analyysi kohteesta
    analysis_id (int, optional): Analysis-taulun ID, johon riskianalyysi liitetään
    
    Returns:
    str: JSON-muotoinen analyysi riskeistä
    """
    # Lataa promptin tiedostosta
    prompt_tiedosto = "prompt_riski.txt"
    with open(prompt_tiedosto, "r") as tiedosto:
        prompt = tiedosto.read()

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
            json_result = json.dumps(json_data)
            
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
                            risk_data=json_result
                        )
                        db.session.add(new_risk)
                        logger.info(f"Luotiin uusi riskianalyysi analyysille {analysis_id}")
                    
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
            return json.dumps(default_json)
    
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
        return json.dumps(default_json)
    