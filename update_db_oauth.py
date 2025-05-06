"""
Tämä skripti päivittää tietokannan lisäämällä OAuth-taulun ja päivittämällä User-taulua
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy_utils import JSONType
from sqlalchemy import text
from config import get_config
import logging
import os
import sys
import stat

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.from_object(get_config())

# Alustetaan tietokanta
db = SQLAlchemy(app)

# Alustetaan migraatiot
migrate = Migrate(app, db)

# Tietokannan taulujen määrittelyt
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    # Lisätään OAuth-kentät
    is_oauth_user = db.Column(db.Boolean, default=False)
    oauth_provider = db.Column(db.String(20), nullable=True)

class OAuth(db.Model):
    """Google OAuth tiedot käyttäjälle"""
    __tablename__ = 'oauth'
    
    id = db.Column(db.Integer, primary_key=True)
    provider = db.Column(db.String(50), nullable=False)
    provider_user_id = db.Column(db.String(256), nullable=False, unique=True)
    token = db.Column(JSONType, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    created_at = db.Column(db.TIMESTAMP, server_default=db.func.current_timestamp())

def update_database():
    """Päivittää tietokannan lisäämällä uudet taulut ja sarakkeet"""
    try:
        with app.app_context():
            # Tarkista että sarakkeet tai taulut puuttuvat ennen päivitystä
            inspector = db.inspect(db.engine)
            
            # Tarkista onko 'oauth' taulu jo olemassa
            tables = inspector.get_table_names()
            if 'oauth' not in tables:
                logger.info("Lisätään 'oauth' taulu...")
                OAuth.__table__.create(db.engine)
                logger.info("'oauth' taulu lisätty onnistuneesti!")
            else:
                logger.info("'oauth' taulu on jo olemassa.")
                
            # Tarkista onko 'is_oauth_user' ja 'oauth_provider' sarakkeet jo käyttäjätaulussa
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Lisää is_oauth_user jos sitä ei ole
            if 'is_oauth_user' not in columns:
                logger.info("Lisätään 'is_oauth_user' sarake käyttäjätauluun...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN is_oauth_user BOOLEAN DEFAULT FALSE"))
                    conn.commit()
                logger.info("'is_oauth_user' sarake lisätty onnistuneesti!")
            else:
                logger.info("'is_oauth_user' sarake on jo olemassa.")
                
            # Lisää oauth_provider jos sitä ei ole
            if 'oauth_provider' not in columns:
                logger.info("Lisätään 'oauth_provider' sarake käyttäjätauluun...")
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users ADD COLUMN oauth_provider VARCHAR(20)"))
                    conn.commit()
                logger.info("'oauth_provider' sarake lisätty onnistuneesti!")
            else:
                logger.info("'oauth_provider' sarake on jo olemassa.")
                
            # Päivitetään password_hash-sarake nullable=True, jotta OAuth-käyttäjät voivat kirjautua
            logger.info("Päivitetään 'password_hash' sarake (nullable=True)...")
            with db.engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ALTER COLUMN password_hash DROP NOT NULL"))
                conn.commit()
            logger.info("'password_hash' sarake päivitetty onnistuneesti!")
            
            logger.info("Tietokannan päivitys onnistui!")
    except Exception as e:
        logger.error(f"Virhe tietokannan päivityksessä: {str(e)}")
        raise

def main():
    """Tarkistaa ja valmistelee istuntohakemistot ja tietokannan"""
    logger.info("Alustetaan sovellusta...")
    
    # Varmistetaan että logs-hakemisto on olemassa
    try:
        os.makedirs('logs', exist_ok=True)
        logger.info("Logs-hakemisto valmis")
    except Exception as e:
        logger.error(f"Virhe logs-hakemiston luomisessa: {e}")
    
    # Varmistetaan että flask_session-hakemisto on olemassa ja oikeudet ovat kunnossa
    try:
        session_dir = os.path.join(os.getcwd(), 'flask_session')
        os.makedirs(session_dir, exist_ok=True)
        
        # Asetetaan oikeudet - 700 = vain omistaja voi lukea/kirjoittaa/suorittaa
        os.chmod(session_dir, stat.S_IRWXU)
        
        logger.info(f"Session-hakemisto luotu ja oikeudet asetettu: {session_dir}")
        logger.info(f"Session-hakemiston oikeudet: {oct(os.stat(session_dir).st_mode)}")
    except Exception as e:
        logger.error(f"Virhe session-hakemiston käsittelyssä: {e}")
    
    # Tarkista ja luo analyses-hakemisto, jota käytetään analyysien tallentamiseen
    try:
        analyses_dir = os.path.join(os.getcwd(), 'analyses')
        os.makedirs(analyses_dir, exist_ok=True)
        logger.info("Analyses-hakemisto valmis")
    except Exception as e:
        logger.error(f"Virhe analyses-hakemiston luomisessa: {e}")
    
    # Tarkistetaan että tietokanta URL on ympäristömuuttujissa
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        logger.warning("DATABASE_URL ei ole asetettu ympäristömuuttujissa!")
    else:
        # Korjataan postgres:// alku postgresql:// muotoon
        if db_url.startswith('postgres://'):
            corrected_url = db_url.replace('postgres://', 'postgresql://', 1)
            logger.info("DATABASE_URL korjattu postgresql:// muotoon")
        else:
            logger.info("DATABASE_URL on jo oikeassa muodossa")
    
    # Tarkista Google OAuth asetukset
    client_id = os.environ.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
    redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI')
    
    if not client_id or not client_secret:
        logger.warning("Google OAuth asetukset puuttuvat ympäristömuuttujista!")
    else:
        # Maski arkaluontoisten tietojen näyttämistä varten
        masked_id = f"{client_id[:5]}...{client_id[-5:]}" if client_id and len(client_id) > 10 else "ei asetettu"
        logger.info(f"Google OAuth asetukset: client_id={masked_id}, redirect_uri={redirect_uri}")
    
    # Tarkista istuntoasetukset
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        logger.warning("SECRET_KEY ei ole asetettu ympäristömuuttujissa!")
    else:
        logger.info("SECRET_KEY on asetettu")
    
    logger.info("Valmistelut suoritettu onnistuneesti")
    return 0  # Onnistunut suoritus

if __name__ == "__main__":
    sys.exit(main()) 