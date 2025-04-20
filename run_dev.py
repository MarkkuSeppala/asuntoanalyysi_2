#!/usr/bin/env python
"""
Kehitystilan käynnistysskripti, joka käynnistää sekä Flask-backendin että React-frontendin.
Käytä tätä skriptiä kehitystilassa sovelluksen käynnistämiseen.

Käyttö: python run_dev.py
"""

import os
import subprocess
import sys
import logging

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def main():
    """Pääfunktio, joka käynnistää sovelluksen kehitystilassa"""
    logger.info("Käynnistetään Asuntoanalyysi kehitystilassa (backend + frontend)")
    
    # Tarkista onko React-sovelluksen kansio olemassa
    react_app_dir = os.path.join('static', 'js', 'react-app')
    if not os.path.exists(react_app_dir):
        logger.error(f"React-sovelluksen kansiota ei löydy: {react_app_dir}")
        sys.exit(1)
    
    # Tarkista onko npm asennettu
    try:
        subprocess.run(['npm', '--version'], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.error("Node.js/npm ei ole asennettu tai ei ole saatavilla PATH:issa")
        sys.exit(1)
    
    # Käynnistetään sovellus --with-frontend argumentilla
    try:
        logger.info("Käynnistetään Flask-sovellus frontendin kanssa...")
        subprocess.run([sys.executable, 'app.py', '--with-frontend'], check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Virhe sovelluksen käynnistämisessä: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Sovellus pysäytetty käyttäjän toimesta")

if __name__ == "__main__":
    main() 