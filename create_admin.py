#!/usr/bin/env python3
import sys
import os
import argparse
import logging
from flask import Flask
from models import db, User

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

def create_admin_user(username, email, password):
    """Luo admin-käyttäjän tai päivittää olemassa olevan käyttäjän admin-oikeuksilla"""
    app = create_app()
    
    with app.app_context():
        # Tarkistetaan onko käyttäjä jo olemassa
        existing_user = User.query.filter_by(username=username).first()
        
        if existing_user:
            # Päivitetään käyttäjä admin-käyttäjäksi jos ei vielä ole
            if existing_user.is_admin:
                logger.info(f"Käyttäjä {username} on jo admin-käyttäjä.")
                return
            
            existing_user.is_admin = True
            db.session.commit()
            logger.info(f"Käyttäjä {username} päivitetty admin-käyttäjäksi.")
        else:
            # Luodaan uusi admin-käyttäjä
            user = User(
                username=username,
                email=email,
                password=password,
                is_admin=True
            )
            
            # Lisätään käyttäjä tietokantaan
            db.session.add(user)
            db.session.commit()
            logger.info(f"Uusi admin-käyttäjä {username} luotu onnistuneesti.")

def main():
    """Pääfunktio argumenttien käsittelyyn ja admin-käyttäjän luontiin"""
    parser = argparse.ArgumentParser(description="Luo uusi admin-käyttäjä tai aseta olemassa oleva käyttäjä admin-käyttäjäksi")
    parser.add_argument("--username", "-u", required=True, help="Käyttäjätunnus")
    parser.add_argument("--email", "-e", required=True, help="Sähköpostiosoite")
    parser.add_argument("--password", "-p", required=True, help="Salasana")
    
    args = parser.parse_args()
    
    try:
        create_admin_user(args.username, args.email, args.password)
    except Exception as e:
        logger.error(f"Virhe admin-käyttäjän luonnissa: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 