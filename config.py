import os
from datetime import timedelta
import datetime
import json
 
# Haetaan Google OAuth asetukset ympäristömuuttujista
google_oauth_config = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID", "299087554173-nr6kp1jlb0gqqdn7hdkn6dsndbma467h.apps.googleusercontent.com"),
        "project_id": os.environ.get("GOOGLE_PROJECT_ID", "gold-subset-459012-n4"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET", "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"),
        "redirect_uris": [os.environ.get("GOOGLE_REDIRECT_URI", "https://www.kotiko.io/")]
    }
}

class Config:
    """Perus konfiguraatio kaikille ympäristöille"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kehitys-avain-vaihda-tuotannossa')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Käytä Render.com:n tarjoamaa tietokanta-URL:ää
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Jos DATABASE_URL alkaa "postgres://", muuta se muotoon "postgresql://"
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
    # Tietokantapoolien asetukset, jotka auttavat SSL-virheiden kanssa
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,      # Tarkistaa yhteyden toimivuuden ennen käyttöä
        'pool_recycle': 280,        # Kierrättää yhteydet 280 sekunnin välein (alle Render.com 5min timeout)
        'pool_timeout': 30,         # Yhteyden odotusaika poolituksessa
        'pool_size': 5,             # Yhteyksien määrä poolissa
        'max_overflow': 10,         # Sallittujen lisäyhteyksien määrä
        'connect_args': {
            'connect_timeout': 10,  # Yhteyden muodostamisen timeout
            'keepalives': 1,        # Pitää yhteyttä auki
            'keepalives_idle': 60,  # Idle-aika ennen keepalive-viestiä
            'keepalives_interval': 10, # Aika keepalive-viestien välillä
            'keepalives_count': 5   # Kuinka monta kertaa yritetään
        }
    }
    
    # Google OAuth asetukset
    GOOGLE_OAUTH_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', google_oauth_config["web"]["client_id"])
    GOOGLE_OAUTH_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', google_oauth_config["web"]["client_secret"])
    
    # Asetetaan sessioiden kesto
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # Yleiset säädöt_
    DEBUG = False
    TESTING = False
    
    # Tuotannossa vahvempi salasana
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Tuotannossa voidaan käyttää SSL:ää
    PREFERRED_URL_SCHEME = 'https'
    
    # Evästeet vain HTTPS:n yli
    SESSION_COOKIE_SECURE = True
    
    # Tuotannossa tarvitaan vähemmän lokitusta
    LOG_LEVEL = 'ERROR'
    
    # Tuotannossa CSRF-suojaus
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Sähköpostiasetukset
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@kotiko.io')
    
    # Sivuston URL ja nimi
    SITE_URL = os.environ.get('SITE_URL', 'http://localhost:5000')
    SITE_NAME = 'Kotiko'
    CURRENT_YEAR = datetime.datetime.now().year

class DevelopmentConfig(Config):
    """Kehitysympäristön konfiguraatio"""
    DEBUG = True
    SITE_URL = 'http://localhost:5000'
    SESSION_COOKIE_SECURE = False
    
class TestingConfig(Config):
    """Testausympäristön konfiguraatio"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost/asuntoanalyysi_test')
    WTF_CSRF_ENABLED = False  # Testeissä ei tarvita CSRF-suojausta
    SITE_URL = 'http://localhost:5000'
    SESSION_COOKIE_SECURE = False
    
class ProductionConfig(Config):
    """Tuotantoympäristön konfiguraatio"""
    # Tuotannossa vahvempi salasana
    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # Tuotannossa voidaan käyttää SSL:ää
    PREFERRED_URL_SCHEME = 'https'
    
    # Evästeet vain HTTPS:n yli
    SESSION_COOKIE_SECURE = True
    
    # Tuotannossa tarvitaan vähemmän lokitusta
    LOG_LEVEL = 'ERROR'
    
    # Tuotannossa CSRF-suojaus
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True
    
    # Tuotannon URL
    SITE_URL = os.environ.get('SITE_URL', 'https://kotiko.io')

def get_config():
    """Palauttaa oikean konfiguraation ympäristön perusteella"""
    config_types = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    env = os.environ.get('FLASK_ENV', 'development')
    return config_types.get(env, DevelopmentConfig) 