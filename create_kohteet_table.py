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

def add_risk_level_column():
    """Lisää risk_level-sarake kohteet-tauluun, jos sitä ei ole"""
    app = create_app()
    
    with app.app_context():
        try:
            # Tarkistetaan onko kohteet-taulu olemassa
            inspector = sqlalchemy.inspect(db.engine)
            if 'kohteet' not in inspector.get_table_names():
                logger.error("Kohteet-taulua ei löydy. Aja ensin create_tables-funktio.")
                return False
                
            # Tarkistetaan onko risk_level-sarake jo olemassa
            columns = inspector.get_columns('kohteet')
            column_names = [c['name'] for c in columns]
            
            if 'risk_level' in column_names:
                logger.info("risk_level-sarake on jo olemassa kohteet-taulussa.")
                return True
                
            # Lisätään risk_level-sarake
            logger.info("Lisätään risk_level-sarake kohteet-tauluun...")
            with db.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
                    ALTER TABLE kohteet 
                    ADD COLUMN risk_level NUMERIC(3,1)
                    """))
            
            logger.info("risk_level-sarake lisätty onnistuneesti!")
            return True
            
        except Exception as e:
            logger.error(f"Virhe risk_level-sarakkeen lisäämisessä: {e}")
            return False

if __name__ == "__main__":
    # Suorita migraatio
    if add_risk_level_column():
        logger.info("Migraatio suoritettu onnistuneesti.")
    else:
        logger.error("Migraatio epäonnistui.")
        sys.exit(1) 