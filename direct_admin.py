#!/usr/bin/env python3
import sys
import os
import argparse
import logging
import psycopg2
from psycopg2 import sql
from werkzeug.security import generate_password_hash

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_admin_user(username, email, password):
    """Luo admin-käyttäjän tai päivittää olemassa olevan käyttäjän suoraan tietokantaan"""
    # Hae DATABASE_URL ympäristömuuttujasta
    db_url = os.environ.get('DATABASE_URL')
    
    if not db_url:
        logger.error("DATABASE_URL ympäristömuuttuja puuttuu")
        return False
    
    # Jos URL alkaa "postgres://", muuta se muotoon "postgresql://"
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Jaetaan URL osiin
        # Oletetaan muoto: postgresql://user:password@host:port/dbname
        if db_url.startswith('postgresql://'):
            parts = db_url[len('postgresql://'):]
            user_pass, host_db = parts.split('@')
            
            if ':' in user_pass:
                user, password_part = user_pass.split(':')
            else:
                user = user_pass
                password_part = ''
                
            if '/' in host_db:
                host_port, dbname = host_db.split('/')
            else:
                host_port = host_db
                dbname = ''
                
            if ':' in host_port:
                host, port = host_port.split(':')
            else:
                host = host_port
                port = '5432'  # Oletusportti
            
            # Muodostetaan yhteys tietokantaan
            conn = psycopg2.connect(
                dbname=dbname,
                user=user,
                password=password_part,
                host=host,
                port=port
            )
        else:
            # Jos URL ei ole odotetun muotoinen, käytä sitä sellaisenaan
            conn = psycopg2.connect(db_url)
        
        # Luodaan cursor tietokantakyselyitä varten
        cur = conn.cursor()
        
        # Tarkistetaan onko käyttäjä jo olemassa
        cur.execute("SELECT id, is_admin FROM users WHERE username = %s", (username,))
        user_exists = cur.fetchone()
        
        if user_exists:
            user_id, is_admin = user_exists
            # Päivitetään käyttäjä admin-käyttäjäksi jos ei vielä ole
            if is_admin:
                logger.info(f"Käyttäjä {username} on jo admin-käyttäjä.")
                conn.close()
                return True
            
            cur.execute("UPDATE users SET is_admin = TRUE WHERE id = %s", (user_id,))
            conn.commit()
            logger.info(f"Käyttäjä {username} päivitetty admin-käyttäjäksi.")
        else:
            # Luodaan uusi admin-käyttäjä
            password_hash = generate_password_hash(password)
            cur.execute(
                "INSERT INTO users (username, email, password_hash, is_admin, created_at, is_active) VALUES (%s, %s, %s, TRUE, CURRENT_TIMESTAMP, TRUE)",
                (username, email, password_hash)
            )
            conn.commit()
            logger.info(f"Uusi admin-käyttäjä {username} luotu onnistuneesti.")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Virhe tietokantayhteydessä: {e}")
        return False

def main():
    """Pääfunktio argumenttien käsittelyyn ja admin-käyttäjän luontiin"""
    parser = argparse.ArgumentParser(description="Luo uusi admin-käyttäjä tai aseta olemassa oleva käyttäjä admin-käyttäjäksi")
    parser.add_argument("--username", "-u", required=True, help="Käyttäjätunnus")
    parser.add_argument("--email", "-e", required=True, help="Sähköpostiosoite")
    parser.add_argument("--password", "-p", required=True, help="Salasana")
    
    args = parser.parse_args()
    
    try:
        success = create_admin_user(args.username, args.email, args.password)
        if not success:
            sys.exit(1)
    except Exception as e:
        logger.error(f"Virhe admin-käyttäjän luonnissa: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
