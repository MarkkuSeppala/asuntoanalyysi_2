from openai import OpenAI
import os
import json
import logging

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

def riskianalyysi(kohde_teksti):
    """
    Analysoi asuntokohteen riskitason OpenAI API:n avulla.
    
    Parameters:
    kohde_teksti (str): API-kutsussa tuotettu analyysi kohteesta
    
    Returns:
    str: JSON-muotoinen analyysi riskeistä
    """
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
                    "text": "Olet kiinteistöalan asiantuntija.\n\nTehtävänäsi on arvioida alla esitellyn kiinteistön riskit ostajalle.\nNäitä riskejä ovat:\n\nLaitteisiin ja rakenteisiin liittyvä riski - Ajanmukaisuus, kunto, korjausvelka\nJälleenmyyntiriski - Kohteen myyntipotentiaali tulevaisuudessa, ostajakunnan laajuus, hintakehityksen epävarmuus\nSijainti- ja alueriski - Alueen kehittyneisyys, mahdolliset negatiiviset mielikuvat tai epävarmuustekijät\nTaloyhtiöriski - Taloyhtiön koko ja koostumus, yhtiön taloudellinen tila, vuokralaisten osuus, hallintotavat\nPisteytä jokainen osa-alue 0-10.\n\nAnna vastaus JSON-muodossa.\n\n<esimerkkivastaus> { \"kohde\": \"Graniittilinnankatu 2 E, Kakola, Turku\", \"kokonaisriskitaso\": 4, \"riskimittari\": [ { \"osa_alue\": \"Laitteisiin ja rakenteisiin liittyvä riski\", \"riski_taso\": 5, \"osuus_prosenttia\": 25, \"kuvaus\": \"Suora sähkölämmitys nostaa energikustannusta. Hiljattain tehty kattava linjasaneeraus pienentää huomattavasti korjauskuluriskiä\" }, { \"osa_alue\": \"Taloyhtiöriski\", \"riski_taso\": 3, \"osuus_prosenttia\": 20, \"kuvaus\": \"Iso yhtiö hajauttaa riskejä, mutta vuokrakäyttöä paljon. Dynaamisuus voi kärsiä.\" }, { \"osa_alue\": \"Asuntokohtainen riski\", \"riski_taso\": 2, \"osuus_prosenttia\": 10, \"kuvaus\": \"Trendikäs ja hyväkuntoinen, mutta hyvin pieni ja käyttömahdollisuudet rajalliset.\" }, { \"osa_alue\": \"Jälleenmyyntiriski\", \"riski_taso\": 4, \"osuus_prosenttia\": 15, \"kuvaus\": \"Pieni ostajakunta ja mahdollinen arvonlasku yhtiölainan vuoksi. Tuottoriski sijoittajalle.\" }, { \"osa_alue\": \"Markkinariski\", \"riski_taso\": 4, \"osuus_prosenttia\": 20, \"kuvaus\": \"Korkeat hinnat ja kilpailu. Pienet asunnot liikkuvat hitaasti, neuvotteluvaraa odotettavissa.\" }, { \"osa_alue\": \"Sijainti- ja alueriski\", \"riski_taso\": 1, \"osuus_prosenttia\": 10, \"kuvaus\": \"Hyvä sijainti ja trendikkyys, mutta alueen kehitys kesken ja mahdollinen stigma.\" } ] } </esimerkkivastaus>\n\n"
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
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        
        # Tarkistetaan saatu vastaus
        json_text = response.text
        logger.info(f"Saatu riskianalyysi: {json_text[:100]}...")
        
        # Varmistetaan että vastaus on validia JSON
        try:
            json_data = json.loads(json_text)
            
            # Validoidaan vastauksen rakenne
            if "kokonaisriskitaso" not in json_data:
                logger.warning("Kokonaisriskitaso puuttuu vastauksesta, lisätään oletusarvo")
                json_data["kokonaisriskitaso"] = 5
                
            if "riskimittari" not in json_data or not isinstance(json_data["riskimittari"], list):
                logger.warning("Riskimittari puuttuu tai ei ole listana, korjataan")
                json_data["riskimittari"] = [
                    {
                        "osa_alue": "Kokonaisriski",
                        "riski_taso": json_data.get("kokonaisriskitaso", 5),
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
            
            # Palautetaan korjattu JSON-teksti
            return json.dumps(json_data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Vastaus ei ole validia JSON: {e}")
            # Palautetaan virheen sijasta yksinkertainen oletusriski JSON
            default_json = {
                "kokonaisriskitaso": 5,
                "riskimittari": [
                    {
                        "osa_alue": "Kokonaisriski",
                        "riski_taso": 5,
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
            "kokonaisriskitaso": 5,
            "riskimittari": [
                {
                    "osa_alue": "Kokonaisriski",
                    "riski_taso": 5,
                    "osuus_prosenttia": 100,
                    "kuvaus": "Kohteen riskitason arviointiin liittyi virhe. Tämä on oletusarvio."
                }
            ]
        }
        return json.dumps(default_json)