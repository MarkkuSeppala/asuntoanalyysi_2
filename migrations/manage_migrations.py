"""
Tietokantamigraatioiden hallintaskripti
Käyttö:
- Migraatioiden alustus: python migrations/manage_migrations.py init
- Migraation luonti: python migrations/manage_migrations.py migrate "Migraation kuvaus"
- Migraation suoritus: python migrations/manage_migrations.py upgrade
"""

import os
import sys
import logging
from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade

# Lisää projektin juurihakemisto Python-polkuun
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Vasta nyt importoidaan models-moduuli
from models import db

# Konfiguroi logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_app():
    """Luo ja konfiguroi Flask-sovellus migraatioita varten"""
    app = Flask(__name__)
    
    # Määritä tietokannan URI ympäristömuuttujasta tai käytä oletusta
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///../flask_database.db')
    
    # Jos käytetään Render.com:in PostgreSQL-tietokantaa, korjaa URL-formaatti
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Alusta tietokanta ja migraatiot
    db.init_app(app)
    migrate = Migrate(app, db)
    
    return app, migrate

def main():
    """Pääfunktio komentojen käsittelyyn"""
    if len(sys.argv) < 2:
        print("Käyttö: python manage_migrations.py [init|migrate|upgrade|manual]")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    app, migrate_manager = create_app()
    
    with app.app_context():
        if command == 'init':
            logger.info("Alustetaan migraatioympäristö...")
            # Huomaa että tässä directory on vain "migrations" ilman /versions-osaa
            # Alustus luo automaattisesti versions-hakemiston
            init(directory="migrations")
            logger.info("Migraatioympäristö alustettu.")
            
        elif command == 'migrate':
            message = sys.argv[2] if len(sys.argv) > 2 else "Automaattinen migraatio"
            logger.info(f"Luodaan migraatio: {message}")
            # Huomaa että tässä directory on "migrations", ei "migrations/versions"
            migrate(message=message, directory="migrations")
            logger.info("Migraatio luotu.")
            
        elif command == 'upgrade':
            logger.info("Päivitetään tietokanta uusimpaan versioon...")
            # Huomaa että tässä directory on "migrations", ei "migrations/versions"
            upgrade(directory="migrations")
            logger.info("Tietokanta päivitetty.")
            
        elif command == 'manual':
            logger.info("Suoritetaan vain migration/versions/payment_system_01.py -tiedosto...")
            from migrations.versions.payment_system_01 import upgrade as manual_upgrade
            manual_upgrade()
            logger.info("Manuaalinen migraatio suoritettu.")
            
        else:
            print(f"Tuntematon komento: {command}")
            print("Käyttö: python manage_migrations.py [init|migrate|upgrade|manual]")
            sys.exit(1)

if __name__ == "__main__":
    main() 