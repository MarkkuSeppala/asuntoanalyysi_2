#!/usr/bin/env python3
import sys
import os
import logging
from flask import Flask
import sqlalchemy
from sqlalchemy import text
from models import db, Kohde

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_app():
    """Luo ja konfiguroi Flask-sovelluksen"""
    app = Flask(__name__)
    
    # Lataa konfigurointi
    from config import get_config
    app.config.from_object(get_config())
    
    # Alustetaan tietokanta
    db.init_app(app)
    
    return app

def create_kohteet_table():
    """Luo kohteet-taulun tietokantaan"""
    app = create_app()
    
    with app.app_context():
        # Tarkista onko taulu jo olemassa
        inspector = sqlalchemy.inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'kohteet' in tables:
            logger.info("Taulu 'kohteet' on jo olemassa.")
            return True
        
        logger.info("Luodaan kohteet-taulu...")
        
        # Suorita SQL-kysely taulun luomiseksi
        try:
            # Luodaan taulu käyttäen SQLAlchemyn create_all-funktiota
            db.create_all()
            logger.info("Kohteet-taulu luotu onnistuneesti SQLAlchemylla!")
            return True
            
        except Exception as e:
            logger.error(f"Virhe taulun luomisessa SQLAlchemylla: {e}")
            
            # Kokeillaan suoraa SQL-kyselyä, jos SQLAlchemy ei toimi
            try:
                with db.engine.connect() as conn:
                    with conn.begin():
                        conn.execute(text("""
                        CREATE TABLE kohteet (
                            id SERIAL PRIMARY KEY,
                            osoite VARCHAR(255) NOT NULL,
                            tyyppi VARCHAR(50),
                            hinta NUMERIC,
                            rakennusvuosi INTEGER,
                            analysis_id INTEGER,
                            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
                            FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE SET NULL
                        )
                        """))
                logger.info("Kohteet-taulu luotu onnistuneesti suoralla SQL-kyselyllä!")
                return True
                
            except Exception as e2:
                logger.error(f"Virhe taulun luomisessa suoralla SQL-kyselyllä: {e2}")
                return False

if __name__ == "__main__":
    success = create_kohteet_table()
    sys.exit(0 if success else 1) 