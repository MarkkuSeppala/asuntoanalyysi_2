"""
Tämä migraatioskripti lisää 'neliot' ja 'huoneet' sarakkeet Kohde-tauluun.
Suorita tämä skripti, jos käytät olemassa olevaa tietokantaa.
"""

from flask import Flask
from models import db, Kohde
import os
from sqlalchemy import Column, Numeric, Integer

# Luo Flask-sovellus
app = Flask(__name__)

# Konfiguroi tietokanta
basedir = os.path.abspath(os.path.dirname(__file__))
# Vaihda tämä vastaamaan todellista tietokantapolkuasi
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, '..', 'asuntoanalyysi.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Alusta tietokanta
db.init_app(app)

def run_migration():
    """Lisää 'neliot' ja 'huoneet' sarakkeet tietokantaan"""
    with app.app_context():
        # Tarkista onko sarakkeita jo olemassa
        inspector = db.inspect(db.engine)
        columns = inspector.get_columns('kohteet')
        column_names = [col['name'] for col in columns]
        
        # Lisää 'neliot'-sarake jos sitä ei ole
        if 'neliot' not in column_names:
            print("Lisätään 'neliot' sarake...")
            db.engine.execute('ALTER TABLE kohteet ADD COLUMN neliot REAL')
            print("'neliot' sarake lisätty.")
        else:
            print("'neliot' sarake on jo olemassa.")
            
        # Lisää 'huoneet'-sarake jos sitä ei ole
        if 'huoneet' not in column_names:
            print("Lisätään 'huoneet' sarake...")
            db.engine.execute('ALTER TABLE kohteet ADD COLUMN huoneet INTEGER')
            print("'huoneet' sarake lisätty.")
        else:
            print("'huoneet' sarake on jo olemassa.")

if __name__ == '__main__':
    print("Aloitetaan migraatio...")
    run_migration()
    print("Migraatio valmis.") 