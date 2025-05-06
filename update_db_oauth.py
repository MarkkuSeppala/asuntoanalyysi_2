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

# Asetetaan lokitus
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
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

if __name__ == "__main__":
    update_database() 