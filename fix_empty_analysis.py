"""
Tämä skripti tarkistaa ja korjaa analyysi-tietokannasta mahdolliset tyhjät analyysi-sisällöt.
"""

import os
import sys
from flask import Flask
from models import db, Analysis, RiskAnalysis
from config import get_config
import logging

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("fix_analyses.log")
    ]
)
logger = logging.getLogger(__name__)

# Luodaan Flask-sovellus ja alustetaan tietokanta
app = Flask(__name__)
app.config.from_object(get_config())
db.init_app(app)

def fix_empty_analyses():
    """Tarkistaa ja korjaa tyhjät analyysit tietokannassa."""
    with app.app_context():
        # Haetaan analyysit joissa sisältö on tyhjä tai NULL
        empty_analyses = db.session.query(Analysis).filter(
            (Analysis.content.is_(None)) | 
            (Analysis.content == '')
        ).all()
        
        logger.info(f"Löydettiin {len(empty_analyses)} analyysiä joissa on tyhjä sisältö")
        
        for analysis in empty_analyses:
            logger.info(f"Tarkistetaan analyysi ID {analysis.id}, otsikko: {analysis.title}")
            
            # Tarkista onko analyysi-tiedosto olemassa
            filepath = None
            if analysis.filename:
                filepath = os.path.join("analyses", analysis.filename)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, "r", encoding="utf-8") as file:
                            content = file.read()
                            # Etsi varsinainen analyysi-osuus
                            if "## ANALYYSI" in content:
                                parts = content.split("## ANALYYSI")
                                if len(parts) > 1:
                                    analysis_content = parts[1].strip()
                                    if analysis_content:
                                        # Päivitä tietokanta
                                        analysis.content = analysis_content
                                        logger.info(f"Päivitetään analyysi ID {analysis.id} tiedostosta, sisällön pituus: {len(analysis_content)} merkkiä")
                                        db.session.commit()
                                        continue
                    except Exception as e:
                        logger.error(f"Virhe luettaessa tiedostoa {filepath}: {e}")
            
            # Jos tiedostoa ei ole tai siitä ei löydy sisältöä, merkitse virhe
            logger.warning(f"Ei voitu korjata analyysiä ID {analysis.id}, asetetaan virheilmoitus")
            analysis.content = "Tämä on virheellinen analyysi. Sisältö on kadonnut tai sitä ei ole koskaan luotu."
            db.session.commit()
        
        # Tarkistetaan myös muut analyysit ja varmistetaan että sisältö ei ole tyhjä
        all_analyses = Analysis.query.all()
        problems_fixed = 0
        
        for analysis in all_analyses:
            if not analysis.content or analysis.content.strip() == "":
                logger.warning(f"Analyysissä ID {analysis.id} on tyhjä sisältö vaikka sitä ei tunnistettu aiemmin")
                analysis.content = "Tämä on virheellinen analyysi. Sisältö on tyhjä."
                db.session.commit()
                problems_fixed += 1
        
        logger.info(f"Korjattiin yhteensä {problems_fixed} muuta ongelmaa")
        
        # Raportoi korjausten yhteenveto
        empty_after = db.session.query(Analysis).filter(
            (Analysis.content.is_(None)) | 
            (Analysis.content == '')
        ).count()
        
        logger.info(f"Korjausten jälkeen tietokannassa on {empty_after} tyhjää analyysiä.")
        return f"Korjattu {len(empty_analyses)} analyysiä, {empty_after} tyhjää analyysiä jäljellä."

if __name__ == "__main__":
    logger.info("Aloitetaan tyhjien analyysien korjaus")
    result = fix_empty_analyses()
    logger.info(f"Korjaus valmis: {result}")
    print(result) 