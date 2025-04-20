import os
from datetime import timedelta
 
class Config:
    """Perus konfiguraatio kaikille ympäristöille"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'kehitys-avain-vaihda-tuotannossa')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Käytä Render.com:n tarjoamaa tietokanta-URL:ää
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Jos DATABASE_URL alkaa "postgres://", muuta se muotoon "postgresql://"
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)
    
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
    
    # Tuotannossa CSRF-suojaus
    WTF_CSRF_ENABLED = True
    SESSION_COOKIE_HTTPONLY = True

def get_config():
    """Palauttaa oikean konfiguraation ympäristön perusteella"""
    config_types = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig
    }
    
    env = os.environ.get('FLASK_ENV', 'development')
    return config_types.get(env, DevelopmentConfig) 