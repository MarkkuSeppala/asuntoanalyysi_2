#!/usr/bin/env python3
import sys
import os
import argparse
import logging
import subprocess

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def create_admin_user(username, email, password):
    """Luo admin-käyttäjän tai päivittää olemassa olevan käyttäjän suoraan tietokantaan käyttäen SQL-komentoja"""
    try:
        # SQL-lauseke käyttäjän tarkistamiseen
        check_sql = f"SELECT id, is_admin FROM users WHERE username = '{username}';"
        
        # Toteuta käyttäen psql-komentoa
        db_url = os.environ.get('DATABASE_URL')
        if not db_url:
            logger.error("DATABASE_URL ympäristömuuttuja puuttuu")
            return False
            
        # Suorita SQL-komento psql:llä
        check_cmd = f'psql "{db_url}" -c "{check_sql}" -t'
        logger.info(f"Tarkistetaan käyttäjä: {username}")
        
        result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
        output = result.stdout.strip()
        
        if result.returncode != 0:
            logger.error(f"Virhe tietokantakyselyssä: {result.stderr}")
            return False
        
        # Jos käyttäjä löytyy
        if output:
            parts = output.split('|')
            if len(parts) >= 2:
                user_id = parts[0].strip()
                is_admin = parts[1].strip() == 't'  # t = true, f = false PostgreSQL:ssä
                
                if is_admin:
                    logger.info(f"Käyttäjä {username} on jo admin-käyttäjä.")
                    return True
                
                # Päivitä käyttäjäksi admin
                update_sql = f"UPDATE users SET is_admin = TRUE WHERE id = {user_id};"
                update_cmd = f'psql "{db_url}" -c "{update_sql}"'
                
                update_result = subprocess.run(update_cmd, shell=True, capture_output=True, text=True)
                if update_result.returncode != 0:
                    logger.error(f"Virhe käyttäjän päivittämisessä: {update_result.stderr}")
                    return False
                
                logger.info(f"Käyttäjä {username} päivitetty admin-käyttäjäksi.")
                return True
        
        # Jos käyttäjää ei löydy, luo uusi
        # Generoidaan salasanan tiiviste käyttäen OpenSSL:ää (yksinkertaistettu, ei yhtä turvallinen kuin werkzeug)
        hash_cmd = f'echo -n "{password}" | openssl dgst -sha256 -hex'
        hash_result = subprocess.run(hash_cmd, shell=True, capture_output=True, text=True)
        if hash_result.returncode != 0:
            logger.error(f"Virhe salasanan tiivisteen luomisessa: {hash_result.stderr}")
            return False
            
        password_hash = hash_result.stdout.strip().split('= ')[1]
        
        # Luodaan SQL-lauseke uuden käyttäjän lisäämiseksi
        insert_sql = f"""
        INSERT INTO users 
        (username, email, password_hash, is_admin, created_at, is_active) 
        VALUES 
        ('{username}', '{email}', '{password_hash}', TRUE, CURRENT_TIMESTAMP, TRUE);
        """
        
        insert_cmd = f'psql "{db_url}" -c "{insert_sql}"'
        insert_result = subprocess.run(insert_cmd, shell=True, capture_output=True, text=True)
        
        if insert_result.returncode != 0:
            logger.error(f"Virhe käyttäjän lisäämisessä: {insert_result.stderr}")
            return False
            
        logger.info(f"Uusi admin-käyttäjä {username} luotu onnistuneesti.")
        return True
        
    except Exception as e:
        logger.error(f"Odottamaton virhe: {e}")
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
