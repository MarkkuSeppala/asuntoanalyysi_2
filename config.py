import os
from datetime import timedelta

class Config:
    """Sovelluksen yleiset konfiguraatiot"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kehitysavain123456789')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Asetetaan sessioiden kesto
    PERMANENT_SESSION_LIFETIME = timedelta(days=30)
    
    # Yleiset säädöt
    DEBUG = False
    TESTING = False
    
    # PostgreSQL -tietokanta
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost/asuntoanalyysi')

class DevelopmentConfig(Config):
    """Kehitysympäristön konfiguraatio"""
    DEBUG = True
    
class TestingConfig(Config):
    """Testausympäristön konfiguraatio"""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL', 'postgresql://postgres:postgres@localhost/asuntoanalyysi_test')
    WTF_CSRF_ENABLED = False  # Testeissä ei tarvita CSRF-suojausta
    
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

# Konfiguraatioiden valinta ympäristömuuttujan perusteella
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    
    # Oletuskonfiguraatio
    'default': DevelopmentConfig
}

def get_config():
    """Palauttaa käytettävän konfiguraation ympäristön perusteella"""
    env = os.environ.get('FLASK_ENV', 'default')
    return config.get(env, config['default']) 