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
    logger.info(f"Aloitetaan riskianalyysi analyysille {analysis_id}, käyttäjälle {user_id}")
    
    # Luodaan yksilöllinen sessiotunniste tätä pyyntöä varten
    import uuid
    request_id = str(uuid.uuid4())
    logger.info(f"Riskianalyysin pyyntö-ID: {request_id}")
    
    # Käyttäjän varmistus
    effective_user_id = user_id
    if not effective_user_id and current_user and hasattr(current_user, 'id') and current_user.id:
        effective_user_id = current_user.id
        logger.info(f"Käyttäjä ID haettu current_user:sta: {effective_user_id}")
    
    # Varmistetaan analysis_id ja user_id yhdistelmän oikeellisuus
    if analysis_id and effective_user_id:
        try:
            # Tarkistetaan kuuluuko analyysi käyttäjälle
            analysis = Analysis.query.get(analysis_id)
            if analysis and analysis.user_id != effective_user_id:
                logger.warning(f"Analyysi {analysis_id} ei kuulu käyttäjälle {effective_user_id}, vaan käyttäjälle {analysis.user_id}")
                # Etsi oikea analyysi käyttäjälle, jos mahdollista
                correct_analysis = None
                if hasattr(analysis, 'property_url') and analysis.property_url:
                    correct_analysis = Analysis.query.filter_by(
                        property_url=analysis.property_url,
                        user_id=effective_user_id
                    ).first()
                
                if correct_analysis:
                    logger.info(f"Löydettiin käyttäjälle {effective_user_id} kuuluva analyysi samalle kohteelle: {correct_analysis.id}")
                    analysis_id = correct_analysis.id
        except Exception as auth_err:
            logger.error(f"Virhe analyysi-käyttäjä-tarkistuksessa: {auth_err}")
    
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
        logger.info(f"Tehdään riskianalyysi käyttäjälle {effective_user_id}, analyysille {analysis_id}, pyyntö {request_id}")
        
        # Luodaan yksilöllinen session ID tätä riskianalyysiä varten
        session_id = str(uuid.uuid4())
        logger.info(f"Riskianalyysin session ID: {session_id}")
        
        # Kokeillaan 3 kertaa, jos OpenAI API epäonnistuu
        max_retries = 3
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
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
                
                # Onnistui, jatketaan käsittelyä
                break
                
            except Exception as api_error:
                retry_count += 1
                last_error = api_error
                wait_time = 2 ** retry_count  # Eksponentiaalinen viive
                logger.warning(f"OpenAI API-virhe riskianalyysissa (yritys {retry_count}/{max_retries}): {api_error}")
                logger.info(f"Odotetaan {wait_time}s ennen uudelleenyritystä")
                
                if retry_count >= max_retries:
                    logger.error(f"OpenAI API-virhe riskianalyysissa, kaikki yritykset epäonnistuivat: {last_error}")
                    # Luodaan virhevastaus
                    import datetime
                    default_json = {
                        "kokonaisriskitaso": 5.0,
                        "riskimittari": [
                            {
                                "osa_alue": "Kokonaisriski",
                                "riski_taso": 5.0,
                                "osuus_prosenttia": 100,
                                "kuvaus": "OpenAI API-virhe: riskitasoa ei voitu määrittää. Tämä on oletusarvio."
                            }
                        ],
                        "meta": {
                            "user_id": effective_user_id,
                            "analysis_id": analysis_id,
                            "error": str(last_error),
                            "request_id": request_id,
                            "timestamp": str(datetime.datetime.now())
                        }
                    }
                    return json.dumps(default_json, ensure_ascii=False)
                
                # Odota ennen uudelleenyritystä
                import time
                time.sleep(wait_time)
        
        # Tarkistetaan saatu vastaus
        json_text = response.output_text
        logger.info(f"Saatu riskianalyysi sessionille {session_id}, pyyntö {request_id}: {json_text[:100]}...")
        
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
            
            # Lisätään metadata tunnistusta varten
            import datetime
            json_data["meta"] = {
                "user_id": effective_user_id,
                "analysis_id": analysis_id,
                "session_id": session_id,
                "request_id": request_id,
                "timestamp": str(datetime.datetime.now())
            }
            
            # Muodostetaan JSON-muotoinen tulos
            json_result = json.dumps(json_data, ensure_ascii=False)
            
            # Jos analysis_id on annettu, tallennetaan riskianalyysi tietokantaan
            if analysis_id:
                # Käytämme paikallista tietokantatransaktiohallintaa
                # Tehdään jokaiselle käsittelyvaiheelle oma yritys ja virheenhallinta
                
                # 1. Tarkistetaan olemassa oleva riskianalyysi
                existing_risk = None
                
                try:
                    # Jos käyttäjä ID on tiedossa, etsitään sekä analysis_id että user_id perusteella
                    if effective_user_id:
                        existing_risk = RiskAnalysis.query.filter_by(
                            analysis_id=analysis_id,
                            user_id=effective_user_id
                        ).first()
                    else:
                        # Muuten etsitään vain analysis_id:n perusteella
                        existing_risk = RiskAnalysis.query.filter_by(
                            analysis_id=analysis_id
                        ).first()
                        
                    logger.info(f"Olemassa oleva riskianalyysi haettu: {existing_risk.id if existing_risk else 'ei löytynyt'}")
                except Exception as query_err:
                    logger.error(f"Virhe haettaessa olemassa olevaa riskianalyysiä: {query_err}")
                
                # 2. Päivitetään olemassa oleva tai luodaan uusi riskianalyysi
                try:
                    if existing_risk:
                        # Päivitetään olemassa olevaa riskianalyysiä, tärkeää lisätä user_id jos puuttuu
                        existing_risk.risk_data = json_result
                        if effective_user_id and not existing_risk.user_id:
                            existing_risk.user_id = effective_user_id
                            
                        db.session.commit()
                        logger.info(f"Päivitettiin riskianalyysi {existing_risk.id} analyysille {analysis_id}, käyttäjälle {effective_user_id}")
                    else:
                        # Luodaan uusi riskianalyysi
                        new_risk = RiskAnalysis(
                            analysis_id=analysis_id,
                            risk_data=json_result,
                            user_id=effective_user_id
                        )
                        db.session.add(new_risk)
                        db.session.commit()
                        logger.info(f"Luotiin uusi riskianalyysi analyysille {analysis_id}, käyttäjälle {effective_user_id}")
                except Exception as db_error:
                    db.session.rollback()
                    logger.error(f"Virhe tallennettaessa riskianalyysiä tietokantaan: {db_error}")
                
                # 3. Päivitetään kohteen riskitaso erillisessä transaktioissa
                try:
                    kohde = Kohde.query.filter_by(analysis_id=analysis_id).first()
                    if kohde:
                        try:
                            kohde.risk_level = json_data["kokonaisriskitaso"]
                            db.session.commit()
                            logger.info(f"Päivitettiin kohteen {kohde.id} riskitaso: {kohde.risk_level}")
                        except Exception as kohde_save_err:
                            db.session.rollback()
                            logger.error(f"Virhe tallennettaessa kohteen riskitasoa: {kohde_save_err}")
                except Exception as kohde_err:
                    logger.error(f"Virhe haettaessa kohdetta analyysille {analysis_id}: {kohde_err}")
            
            # Palautetaan korjattu JSON-teksti
            return json_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Vastaus ei ole validia JSON: {e}")
            # Palautetaan virheen sijasta yksinkertainen oletusriski JSON
            import datetime
            default_json = {
                "kokonaisriskitaso": 5.0,
                "riskimittari": [
                    {
                        "osa_alue": "Kokonaisriski",
                        "riski_taso": 5.0,
                        "osuus_prosenttia": 100,
                        "kuvaus": "Kohteen riskitason arviointiin liittyi ongelmia. Tämä on oletusarvio."
                    }
                ],
                "meta": {
                    "user_id": effective_user_id,
                    "analysis_id": analysis_id,
                    "error": "JSON decode error",
                    "request_id": request_id,
                    "timestamp": str(datetime.datetime.now())
                }
            }
            return json.dumps(default_json, ensure_ascii=False)
    
    except Exception as e:
        logger.exception(f"Virhe riskianalyysissä: {e}")
        # Palautetaan virheen sijasta yksinkertainen oletusriski JSON
        import datetime
        default_json = {
            "kokonaisriskitaso": 5.0,
            "riskimittari": [
                {
                    "osa_alue": "Kokonaisriski",
                    "riski_taso": 5.0,
                    "osuus_prosenttia": 100,
                    "kuvaus": "Kohteen riskitason arviointiin liittyi virhe. Tämä on oletusarvio."
                }
            ],
            "meta": {
                "user_id": effective_user_id,
                "analysis_id": analysis_id,
                "error": str(e),
                "request_id": request_id,
                "timestamp": str(datetime.datetime.now())
            }
        }
        return json.dumps(default_json, ensure_ascii=False)
    