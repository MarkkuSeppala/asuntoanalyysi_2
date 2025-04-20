#!/usr/bin/env python3
import sys
import os
import logging
from flask import Flask
import sqlalchemy
from sqlalchemy import text

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
    
    return app

def run_migration():
    """Suorittaa tietokantamigraation"""
    app = create_app()
    
    with app.app_context():
        # Tietokantayhteys
        db_url = app.config['SQLALCHEMY_DATABASE_URI']
        engine = sqlalchemy.create_engine(db_url)
        
        try:
            # Tarkista onko api_calls_count-sarake jo olemassa
            with engine.connect() as conn:
                inspector = sqlalchemy.inspect(engine)
                columns = [col['name'] for col in inspector.get_columns('users')]
                
                if 'api_calls_count' not in columns:
                    logger.info("Lisätään api_calls_count-sarake users-tauluun...")
                    
                    # Lisää api_calls_count-sarake oletusarvolla 0
                    with conn.begin():
                        conn.execute(text("ALTER TABLE users ADD COLUMN api_calls_count INTEGER DEFAULT 0"))
                        
                    logger.info("Sarake lisätty onnistuneesti!")
                else:
                    logger.info("Sarake api_calls_count on jo olemassa.")
                
                return True
                
        except Exception as e:
            logger.error(f"Virhe migraation suorituksessa: {e}")
            return False

if __name__ == "__main__":
    success = run_migration()
    sys.exit(0 if success else 1) 