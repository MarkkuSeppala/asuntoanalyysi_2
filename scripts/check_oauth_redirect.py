#!/usr/bin/env python
"""
Tämä skripti auttaa tarkistamaan Google OAuth redirect URI -asetukset.
Skripti näyttää mitä redirect URI -osoitetta sovellus käyttää ja mitä on 
asetettu ympäristömuuttujiin.
"""

import os
import sys
import requests
import logging
from urllib.parse import urlparse, urljoin

# Aseta lokitustaso
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_redirect_uri(site_url=None):
    """Tarkistaa ja näyttää oikean redirect URI:n annetulle URL:lle"""
    # Tarkista ympäristömuuttujat
    env_redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', 'ei asetettu')
    env_site_url = os.environ.get('SITE_URL', 'ei asetettu')
    
    if not site_url:
        site_url = env_site_url

    # Jos site_url puuttuu edelleen, käytä oletuksia
    if site_url in ['ei asetettu', None]:
        # Koita arvata kehitysympäristön URL
        site_url = 'http://localhost:5000'
        logger.warning(f"SITE_URL ei ole asetettu ympäristömuuttujissa. Käytetään oletusta: {site_url}")
    
    # Generoi oletusarvot Flask-Dance -kirjastolle
    expected_redirect_path = '/login/google/authorized'
    
    # Täysi redirect URI
    full_redirect_uri = urljoin(site_url, expected_redirect_path)
    
    # Tarkista toimiiko osoite
    redirect_uri_reachable = False
    try:
        # HEAD-pyyntö vain tarkistaa onko URL saavutettavissa
        response = requests.head(full_redirect_uri, timeout=3)
        # 404 on ok tässä tilanteessa, se vain varmistaa että osoite on saavutettavissa
        redirect_uri_reachable = response.status_code < 500
    except requests.RequestException:
        redirect_uri_reachable = False
    
    # Tulosta tulokset
    print("\n===== Google OAuth Redirect URI Tarkistus =====")
    print(f"Sovelluksen URL (SITE_URL): {site_url}")
    print(f"Generoidut redirect URI -osoitteet:")
    print(f"  - {full_redirect_uri}")
    print(f"\nYmpäristömuuttujat:")
    print(f"  - GOOGLE_REDIRECT_URI: {env_redirect_uri}")
    print(f"  - SITE_URL: {env_site_url}")
    
    print("\nGoogle Cloud Console -asetukset:")
    print("Varmista, että seuraava osoite on lisätty Google Cloud Console -palvelussa")
    print("OAuth 2.0 -tunnistetietojen 'Authorized redirect URIs' -listaan:")
    print(f"  - {full_redirect_uri}")
    
    if not redirect_uri_reachable:
        print("\nVAROITUS: Redirect URI -osoite ei näytä olevan saavutettavissa.")
        print("Tämä voi johtua siitä, että sovellus ei ole käynnissä tai SITE_URL on väärä.")
    
    print("\nJos saat 'Error 400: redirect_uri_mismatch' -virheen:")
    print("1. Tarkista että täsmälleen oikea redirect URI on lisätty Google Cloud Consolessa")
    print("2. Varmista että GOOGLE_REDIRECT_URI-ympäristömuuttuja on asetettu oikein")
    print("3. Tarkista sovelluksen lokit nähdäksesi mikä osoite lähetetään Googlelle")
    print("\nMuista, että URL-osoitteen pitää täsmätä täsmälleen - http:// vs https:// ja mahdolliset")
    print("loppukauttaviivat ovat tärkeitä.")
    
    # Jos ympäristömuuttuja ei vastaa generoitua URIa, huomauta
    if env_redirect_uri != 'ei asetettu' and env_redirect_uri != full_redirect_uri:
        print("\nHUOMIO: GOOGLE_REDIRECT_URI-ympäristömuuttuja ei vastaa generoitua osoitetta!")
        print(f"Ympäristömuuttuja: {env_redirect_uri}")
        print(f"Generoitu osoite: {full_redirect_uri}")
        print("Tämä voi aiheuttaa 'redirect_uri_mismatch' -virheen!")

    return {
        'site_url': site_url,
        'full_redirect_uri': full_redirect_uri,
        'env_redirect_uri': env_redirect_uri,
        'env_site_url': env_site_url,
        'redirect_uri_reachable': redirect_uri_reachable
    }

if __name__ == "__main__":
    # Tarkista onko komentoriviparametreja
    site_url = None
    if len(sys.argv) > 1:
        site_url = sys.argv[1]
        
    check_redirect_uri(site_url) 