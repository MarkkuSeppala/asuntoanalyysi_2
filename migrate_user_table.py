#!/usr/bin/env python3
import os
import sys
import logging
import sqlalchemy
from sqlalchemy import text
from config import get_config
from flask import Flask

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Luodaan Flask-sovellus migraatiota varten
app = Flask(__name__)
app.config.from_object(get_config())

def migrate_user_table():
    """Lisää käyttäjä-tauluun uudet kentät"""
    try:
        # Luodaan yhteys tietokantaan
        engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        
        with engine.connect() as conn:
            # Tarkistetaan ensin onko kentät jo olemassa
            inspector = sqlalchemy.inspect(engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            # Lisätään vain kentät, joita ei vielä ole
            new_columns = [
                ('first_name', 'character varying(80) NOT NULL'),
                ('last_name', 'character varying(80) NOT NULL'),
                ('street_address', 'character varying(120) NOT NULL'),
                ('postal_code', 'character varying(10) NOT NULL'),
                ('city', 'character varying(80) NOT NULL'),
                ('state', 'character varying(80) NOT NULL'),
                ('country', 'character varying(80) NOT NULL'),
            ]
            
            for col_name, col_type in new_columns:
                if col_name not in columns:
                    # Lisätään uusi sarake
                    alter_sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"
                    
                    # Olemassa olevat tietueet: aseta oletusarvot
                    default_value = "''" if "varying" in col_type else "'Suomi'" if col_name == 'country' else "''"
                    update_sql = f"UPDATE users SET {col_name} = {default_value};"
                    
                    # Suorita lausekkeet
                    logger.info(f"Lisätään sarake: {col_name}")
                    conn.execute(text(alter_sql))
                    
                    logger.info(f"Päivitetään olemassa olevat tietueet")
                    conn.execute(text(update_sql))
                    
                    # Commitoidaan muutokset
                    conn.commit()
            
        logger.info("Käyttäjätaulun migraatio suoritettu onnistuneesti!")
        return True
    
    except Exception as e:
        logger.error(f"Virhe käyttäjätaulun migraatiossa: {e}")
        return False

if __name__ == "__main__":
    print("Aloitetaan käyttäjätaulun migraatio")
    success = migrate_user_table()
    
    if success:
        print("Migraatio onnistui!")
        sys.exit(0)
    else:
        print("Migraatio epäonnistui. Tarkista lokitiedostot.")
        sys.exit(1) 