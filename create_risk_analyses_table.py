#!/usr/bin/env python3
import sys
import os
import logging
import psycopg2
from config import get_config

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_risk_analyses_table():
    """Luo risk_analyses taulun tietokantaan jos se puuttuu"""
    conn = None
    try:
        # Haetaan tietokantayhteyden parametrit
        config = get_config()
        
        # Yhdistetään tietokantaan
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Tarkistetaan onko risk_analyses-taulu jo olemassa
        cursor.execute("SELECT to_regclass('public.risk_analyses')")
        exists = cursor.fetchone()[0]
        
        if exists:
            logger.info("Taulu risk_analyses on jo olemassa.")
            return True
        
        # Luodaan risk_analyses-taulu
        logger.info("Luodaan risk_analyses-taulu...")
        
        create_table_sql = """
        CREATE TABLE risk_analyses (
            id SERIAL PRIMARY KEY,
            analysis_id INTEGER NOT NULL,
            risk_data TEXT NOT NULL,
            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
            FOREIGN KEY (analysis_id) REFERENCES analyses (id) ON DELETE CASCADE
        )
        """
        
        cursor.execute(create_table_sql)
        
        # Vahvistetaan muutokset
        conn.commit()
        logger.info("risk_analyses-taulu luotu onnistuneesti!")
        
        return True
        
    except (Exception, psycopg2.DatabaseError) as error:
        logger.error(f"Virhe taulun luomisessa: {error}")
        return False
    finally:
        if conn is not None:
            conn.close()

if __name__ == "__main__":
    # Suorita taulun luonti
    success = create_risk_analyses_table()
    
    if success:
        logger.info("Taulun luonti suoritettu onnistuneesti.")
        sys.exit(0)
    else:
        logger.error("Taulun luonti epäonnistui.")
        sys.exit(1)
