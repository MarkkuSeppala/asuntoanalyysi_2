import os
import logging
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, send_file, abort
import api_call
from flask_login import LoginManager, current_user, login_required
from models import db, User, Analysis, RiskAnalysis, Kohde
from auth import auth
from config import get_config
from datetime import datetime
import sqlalchemy
from riskianalyysi import riskianalyysi
import json
import sys
import re
import traceback
import time
import etuovi_downloader  # Import the etuovi_downloader
import oikotie_downloader  # Import the oikotie_downloader
import tempfile
import kat_api_call  # Import the kat_api_call module
from sqlalchemy import text

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Lisätään tiedostolokitus
try:
    # Varmistetaan että logs-hakemisto on olemassa
    os.makedirs('logs', exist_ok=True)
    
    file_handler = logging.FileHandler('logs/app.log')
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
except Exception as e:
    print(f"Varoitus: Lokitiedostoa ei voitu avata: {e}")
    # Jatketaan ilman tiedostolokitusta

app = Flask(__name__)

# Asetetaan sovelluksen konfigurointi
app.config.from_object(get_config())

# Alustetaan tietokanta
db.init_app(app)

# Alustetaan kirjautumisenhallinta
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Kirjaudu sisään käyttääksesi tätä sivua.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """Lataa käyttäjä session tunnisteen perusteella"""
    return User.query.get(int(user_id))

# Rekisteröidään blueprint-komponentit
app.register_blueprint(auth, url_prefix='/auth')

# Luodaan tietokantafunktio, joka suoritetaan ennen ensimmäistä pyyntöä
def create_tables():
    """Luo tietokanta ja taulut jos ne eivät ole olemassa"""
    with app.app_context():
        db.create_all()
        
        # Varmistetaan että kohteet-taulu on luotu oikein
        inspector = sqlalchemy.inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Tarkista onko kohteet-taulu jo olemassa
        if 'kohteet' not in tables:
            logger.info("Kohteet-taulu puuttuu. Luodaan se...")
            try:
                # Luodaan taulu käyttäen create_all-funktiota, joka huomioi kaikki määritellyt mallit
                db.create_all()
                logger.info("Kohteet-taulu luotu onnistuneesti.")
            except Exception as e:
                logger.error(f"Virhe kohteet-taulun luomisessa SQLAlchemylla: {e}")
                
                # Jos SQLAlchemy epäonnistuu, yritetään luoda taulu suoralla SQL-kyselyllä
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
                except Exception as e2:
                    logger.error(f"Virhe kohteet-taulun luomisessa suoralla SQL-kyselyllä: {e2}")
        else:
            # Tarkista onko analysis_id-sarake määritetty ei-null-arvoiseksi
            columns = inspector.get_columns('kohteet')
            # Etsi analysis_id-sarake
            for column in columns:
                if column['name'] == 'analysis_id':
                    if not column.get('nullable', True):
                        logger.info("Päivitetään kohteet-taulun analysis_id-sarake nullable=True")
                        try:
                            with db.engine.connect() as conn:
                                with conn.begin():
                                    conn.execute(text("ALTER TABLE kohteet ALTER COLUMN analysis_id DROP NOT NULL"))
                            logger.info("Kohteet-taulun analysis_id-sarake päivitetty onnistuneesti!")
                        except Exception as e:
                            logger.error(f"Virhe kohteet-taulun päivityksessä: {e}")
                    break

# Varmistetaan että taulut on luotu sovelluksen käynnistyessä
with app.app_context():
    # Tarkista onko tauluja jo olemassa
    inspector = sqlalchemy.inspect(db.engine)
    tables = inspector.get_table_names()
    if not tables:
        logger.info("Tietokanta on tyhjä. Luodaan taulut...")
        db.create_all()
        logger.info("Taulut luotu.")
    else:
        logger.info(f"Tietokanta sisältää jo taulut: {tables}")
    
    # Kutsutaan create_tables-funktiota, joka varmistaa myös kohteet-taulun olemassaolon
    create_tables()

# Lisätään päivämäärä kaikkiin templateihin
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/landing')
def landing():
    """Landing page - sovelluksen markkinointisivu"""
    return render_template('landing.html')

@app.route('/flask')
def flask_index():
    """Flask-pohjainen etusivu, jossa käyttäjä voi syöttää asuntolinkin tai näkee landing-sivun"""
    if current_user.is_authenticated:
        # Haetaan käyttäjän viimeisimmät analyysit
        analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).limit(5).all()
        return render_template('index.html', analyses=analyses)
    else:
        return render_template('landing.html')

# Apufunktiot
def _sanitize_content(content):
    """Sanitoi sisällön, jotta sitä voidaan käyttää turvallisesti template-renderöinnissä"""
    if not content:
        return content
    
    # Poista potentiaalisesti vaaralliset script-tagit
    content = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', content)
    return content

# Funktio joka päättelee URL-tyypin ja hakee asuntotiedot oikealla tavalla
def get_property_data(url):
    """
    Hakee asunnon tiedot URL:n perusteella joko käyttäen oikotie_downloader-moduulia (Oikotie) 
    tai etuovi_downloader-moduulia (Etuovi)
    
    Args:
        url (str): Asuntoilmoituksen URL
        
    Returns:
        tuple: (success, markdown_data, source)
            - success (bool): True jos haku onnistui, False muuten
            - markdown_data (str): Asunnon tiedot markdown-muodossa tai None jos haku epäonnistui
            - source (str): Lähteen nimi ('oikotie' tai 'etuovi')
    """
    # Tarkistetaan URL:n tyyppi
    if 'oikotie.fi' in url or 'asunnot.oikotie.fi' in url:
        # Käytetään Oikotie-downloaderia
        logger.info(f"Oikotie URL havaittu: {url}")
        try:
            # Haetaan asunnon tiedot oikotie_downloader-moduulilla
            logger.info("Haetaan tiedot oikotie_downloader-moduulilla...")
            text_content = oikotie_downloader.get_property_info(url, verbose=False)
            
            # Määritellään property_id
            match = re.search(r'/(\d+)/?$', url)
            property_id = match.group(1) if match else "unknown"
            
            # Muunnetaan teksti markdown-muotoon
            logger.info("Muotoillaan teksti markdown-muotoon...")
            markdown_data = f"""# Oikotie-asuntoilmoitus

## Perustiedot
URL: {url}
Lähde: Oikotie.fi
Ilmoitus-ID: {property_id}

## Ilmoituksen sisältö
{text_content}
"""
            return True, markdown_data, 'oikotie'
            
        except Exception as e:
            logger.error(f"Virhe Oikotie-datan noutamisessa: {e}")
            logger.error(traceback.format_exc())
            return False, None, 'oikotie'
        
    elif 'etuovi.com' in url:
        # Käytetään Etuovi-downloaderia
        logger.info(f"Etuovi URL havaittu: {url}")
        try:
            # Määritellään tiedostonimi
            property_id = url.split('/')[-1]
            pdf_filename = f"etuovi_{property_id}.pdf"
            
            # Ladataan PDF ja muunnetaan tekstiksi
            logger.info("Ladataan PDF Etuovesta...")
            pdf_path = etuovi_downloader.download_pdf(url, pdf_filename, headless=True)
            
            logger.info("Muunnetaan PDF tekstiksi...")
            text_path = etuovi_downloader.convert_pdf_to_text(pdf_path)
            
            # Luetaan tekstitiedosto
            with open(text_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            # Muunnetaan etuovi-teksti markdown-muotoon
            logger.info("Muotoillaan teksti markdown-muotoon...")
            markdown_data = f"""# Etuovi-asuntoilmoitus

## Perustiedot
URL: {url}
Lähde: Etuovi.com
Ilmoitus-ID: {property_id}

## Ilmoituksen sisältö
{text_content}
"""
            
            # Poista tilapäiset tiedostot
            try:
                os.remove(pdf_path)
                os.remove(text_path)
                logger.info("Tilapäiset tiedostot poistettu")
            except Exception as e:
                logger.warning(f"Tilapäisten tiedostojen poistaminen epäonnistui: {e}")
                
            return True, markdown_data, 'etuovi'
            
        except Exception as e:
            logger.error(f"Virhe Etuovi-datan noutamisessa: {e}")
            logger.error(traceback.format_exc())
            return False, None, 'etuovi'
    else:
        # Tuntematon URL-tyyppi
        logger.warning(f"Tuntematon URL-tyyppi: {url}")
        return False, None, 'unknown'

@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Käsittelee käyttäjän syöttämän URL:n ja palauttaa analyysin"""
    try:
        # Tarkistetaan onko käyttäjä oikeutettu tekemään API-kutsun
        if not current_user.can_make_api_call():
            return render_template('error.html', 
                                error_title="API-kutsujen rajoitus", 
                                error_message="Olet käyttänyt kaikki API-kutsusi (2). Päivitä tilisi admin-tasoon jatkaaksesi käyttöä."), 403
        
        # Haetaan URL käyttäjän lomakkeesta
        url = request.form.get('url')
        
        if not url:
            return jsonify({'error': 'URL-osoite puuttuu'}), 400
        
        # Tarkistetaan, että URL on hyväksytty URL (Oikotie tai Etuovi)
        if ('oikotie.fi' not in url and 'asunnot.oikotie.fi' not in url and 
            'etuovi.com' not in url):
            return jsonify({'error': 'Syötä kelvollinen Oikotie- tai Etuovi-asuntolinkin URL'}), 400
        
        # Haetaan asunnon tiedot URL:n perusteella
        logger.info(f"Haetaan tietoja URL:sta: {url}")
        success, markdown_data, source = get_property_data(url)
        
        if not success or not markdown_data:
            logger.error("Asuntoilmoituksen noutaminen epäonnistui")
            return render_template('error.html', 
                                  error_title="Virhe ilmoituksen haussa", 
                                  error_message="Ilmoituksen hakemisessa tapahtui virhe. Ole hyvä, yritä myöhemmin uudelleen."), 500
        
        logger.debug(f"Markdown-datan pituus: {len(markdown_data)} merkkiä")
        
        # Haetaan kohteen perustiedot ensin KAT API:n avulla
        property_data = None
        kohde_id = None
        try:
            logger.info("Haetaan kohteen perustiedot KAT API:lla")
            property_data = kat_api_call.get_property_data(markdown_data)
            
            if property_data:
                # Tallennetaan kohteet-tauluun ilman analysis_id:tä, liitetään myöhemmin
                logger.info("Tallennetaan kohteen tiedot tietokantaan")
                kohde_id = kat_api_call.save_property_data_to_db(property_data)
                if kohde_id:
                    logger.info(f"Kohde tallennettu tietokantaan ID:llä {kohde_id}")
                else:
                    logger.warning("Kohteen tallentaminen epäonnistui")
            else:
                logger.warning("Kohteen perustietoja ei saatu")
        except Exception as e:
            logger.error(f"Virhe kohteen tietojen käsittelyssä: {e}")
            logger.error(traceback.format_exc())
        
        # Käytetään OpenAI API:a analyysin tekemiseen
        logger.info("Tehdään OpenAI API -kutsu analyysia varten")
        analysis_response = api_call.get_analysis(markdown_data, url)
        
        if not analysis_response:
            logger.error("API-kutsu palautti tyhjän vastauksen")
            return jsonify({'error': 'API-analyysi epäonnistui'}), 500
            
        # Varmistetaan että vastaus on puhdistettu (API:ssa puhdistus tehdään jo, tämä on varmuuden vuoksi)
        analysis_response = api_call.sanitize_markdown_response(analysis_response)
        
        # Sanitoidaan sisältö ennen template-renderöintiä_
        sanitized_markdown = _sanitize_content(markdown_data)
        sanitized_analysis = _sanitize_content(analysis_response)
        
        # Kasvatetaan käyttäjän API-kutsujen määrää, jos ei ole admin
        if not current_user.is_admin:
            current_user.increment_api_call_count()
        
        # Haetaan analyysi tietokannasta URL:n perusteella tai luodaan uusi
        analysis = Analysis.query.filter_by(property_url=url, user_id=current_user.id).first()
        analysis_id = None

        if analysis:
            # Käytetään olemassa olevaa analyysiä
            analysis_id = analysis.id
            logger.info(f"Käytetään olemassa olevaa analyysiä ID: {analysis_id}")
        else:
            # Tätä voi tapahtua, koska api_call.get_analysis tallentaa analyysin tietokantaan
            # Yritetään hakea juuri luotu analyysi URL:n perusteella
            analysis = Analysis.query.filter_by(property_url=url, user_id=current_user.id).first()
            if analysis:
                analysis_id = analysis.id
                logger.info(f"Löydettiin juuri luotu analyysi ID: {analysis_id}")

        # Jos meillä on nyt kohde_id ja analysis_id, päivitetään kohteen analysis_id
        if kohde_id and analysis_id:
            try:
                logger.info(f"Päivitetään kohteen {kohde_id} analysis_id = {analysis_id}")
                kohde = Kohde.query.get(kohde_id)
                if kohde:
                    kohde.analysis_id = analysis_id
                    db.session.commit()
                    logger.info("Kohteen analysis_id päivitetty onnistuneesti")
                else:
                    logger.warning(f"Kohdetta ID:llä {kohde_id} ei löytynyt")
            except Exception as e:
                logger.error(f"Virhe kohteen analysis_id:n päivittämisessä: {e}")
                logger.error(traceback.format_exc())

        # Tehdään riskianalyysi API-vastauksesta, jos analyysi on löydetty
        riski_data = None
        if analysis_id:
            try:
                logger.info("Tehdään riskianalyysi kohteesta")
                riski_data_json = riskianalyysi(analysis_response, analysis_id)
                logger.info(f"Saatiin riskianalyysin JSON vastaus pituudella: {len(riski_data_json)}")
                riski_data = json.loads(riski_data_json)
                logger.info(f"Riskianalyysi valmis: {riski_data.get('kokonaisriskitaso', 'N/A')}/10")
            except Exception as e:
                logger.error(f"Virhe riskianalyysissä: {e}")
                logger.error(traceback.format_exc())
        
        # Redirect to the analysis page if we have an analysis ID
        if analysis_id:
            return redirect(url_for('view_analysis', analysis_id=analysis_id))
        else:
            # Renderöidään asunnon tiedot ja analyysi
            return render_template('results.html', 
                            property_data=sanitized_markdown, 
                            analysis=sanitized_analysis,
                              riski_data=riski_data,
                              property_url=url,
                              analysis_id=analysis_id,
                              source=source)
        
    except Exception as e:
        logger.error(f"Virhe asuntoanalyysissa: {e}")
        logger.error(traceback.format_exc())
        return render_template('error.html', 
                              error_title="Virhe analyysissä", 
                              error_message=f"Analysoinnissa tapahtui virhe: {str(e)}"), 500

@app.route('/api/analyze', methods=['POST'])
@login_required
def api_analyze():
    """API-pääte, joka ottaa vastaan URL:n ja palauttaa analyysin JSON-muodossa"""
    try:
        # Tarkistetaan onko käyttäjä oikeutettu tekemään API-kutsun
        if not current_user.can_make_api_call():
            return jsonify({
                'error': 'API-kutsujen rajoitus', 
                'message': 'Olet käyttänyt kaikki API-kutsusi (2). Päivitä tilisi admin-tasoon jatkaaksesi käyttöä.'
            }), 403
        
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL-osoite puuttuu'}), 400
        
        # Tarkistetaan, että URL on hyväksytty URL (Oikotie tai Etuovi)
        if ('oikotie.fi' not in url and 'asunnot.oikotie.fi' not in url and 
            'etuovi.com' not in url):
            return jsonify({'error': 'Syötä kelvollinen Oikotie- tai Etuovi-asuntolinkin URL'}), 400
        
        # Haetaan asunnon tiedot URL:n perusteella
        logger.info(f"Haetaan tietoja URL:sta: {url}")
        success, markdown_data, source = get_property_data(url)
        
        if not success or not markdown_data:
            logger.error("API: Asuntoilmoituksen noutaminen epäonnistui")
            return jsonify({
                'error': 'Ilmoituksen hakemisessa tapahtui virhe', 
                'message': 'Ilmoituksen hakemisessa tapahtui virhe. Ole hyvä, yritä myöhemmin uudelleen.'
            }), 500
        
        # Haetaan kohteen perustiedot ensin KAT API:n avulla
        property_data = None
        kohde_id = None
        try:
            logger.info("API: Haetaan kohteen perustiedot KAT API:lla")
            property_data = kat_api_call.get_property_data(markdown_data)
            
            if property_data:
                # Tallennetaan kohteet-tauluun ilman analysis_id:tä, liitetään myöhemmin
                logger.info("API: Tallennetaan kohteen tiedot tietokantaan")
                kohde_id = kat_api_call.save_property_data_to_db(property_data)
                if kohde_id:
                    logger.info(f"API: Kohde tallennettu tietokantaan ID:llä {kohde_id}")
                else:
                    logger.warning("API: Kohteen tallentaminen epäonnistui")
            else:
                logger.warning("API: Kohteen perustietoja ei saatu")
        except Exception as e:
            logger.error(f"API: Virhe kohteen tietojen käsittelyssä: {e}")
        
        # Käytetään OpenAI API:a analyysin tekemiseen
        analysis_response = api_call.get_analysis(markdown_data, url)
        
        # Varmistetaan että vastaus on puhdistettu (API:ssa puhdistus tehdään jo)
        analysis_response = api_call.sanitize_markdown_response(analysis_response)
        
        # Kasvatetaan käyttäjän API-kutsujen määrää, jos ei ole admin
        if not current_user.is_admin:
            current_user.increment_api_call_count()
        
        # Haetaan analyysi tietokannasta URL:n perusteella tai luodaan uusi
        analysis = Analysis.query.filter_by(property_url=url, user_id=current_user.id).first()
        analysis_id = None
        riski_data = None
        
        if analysis:
            # Käytetään olemassa olevaa analyysiä
            analysis_id = analysis.id
            logger.info(f"API: Käytetään olemassa olevaa analyysiä ID: {analysis_id}")
        else:
            # Tätä voi tapahtua, koska api_call.get_analysis tallentaa analyysin tietokantaan
            # Yritetään hakea juuri luotu analyysi URL:n perusteella
            analysis = Analysis.query.filter_by(property_url=url, user_id=current_user.id).first()
            if analysis:
                analysis_id = analysis.id
                logger.info(f"API: Löydettiin juuri luotu analyysi ID: {analysis_id}")
        
        # Jos meillä on nyt kohde_id ja analysis_id, päivitetään kohteen analysis_id
        if kohde_id and analysis_id:
            try:
                logger.info(f"API: Päivitetään kohteen {kohde_id} analysis_id = {analysis_id}")
                kohde = Kohde.query.get(kohde_id)
                if kohde:
                    kohde.analysis_id = analysis_id
                    db.session.commit()
                    logger.info("API: Kohteen analysis_id päivitetty onnistuneesti")
                else:
                    logger.warning(f"API: Kohdetta ID:llä {kohde_id} ei löytynyt")
            except Exception as e:
                logger.error(f"API: Virhe kohteen analysis_id:n päivittämisessä: {e}")
                
        # Tehdään riskianalyysi API-vastauksesta, jos analyysi on löydetty
        if analysis_id:
            try:
                logger.info("API: Tehdään riskianalyysi kohteesta")
                riski_data_json = riskianalyysi(analysis_response, analysis_id)
                logger.info(f"API: Saatiin riskianalyysin JSON vastaus pituudella: {len(riski_data_json)}")
                riski_data = json.loads(riski_data_json)
                logger.info(f"API: Riskianalyysi valmis: {riski_data.get('kokonaisriskitaso', 'N/A')}/10")
            except Exception as e:
                logger.error(f"API: Virhe riskianalyysissä: {e}")
                riski_data = None
        
        # Palautetaan analyysi, raakatiedot ja riskianalyysi JSON-muodossa
        response_data = {
            'property_data': markdown_data,
            'analysis': analysis_response,
            'source': source
        }
        
        # Lisätään perustiedot vastaukseen, jos ne on saatavilla
        if property_data:
            response_data['basic_property_data'] = property_data
            
        # Lisätään riskianalyysi vastaukseen, jos se on saatavilla
        if riski_data:
            response_data['risk_analysis'] = riski_data
            
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Virhe API-analyysin teossa: {e}")
        return jsonify({'error': f'Virhe: {str(e)}'}), 500

@app.route('/analyses')
@login_required
def list_analyses():
    """Näyttää kirjautuneen käyttäjän tallennetut analyysit"""
    try:
        # Haetaan käyttäjän analyysit tietokannasta
        analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
        
        return render_template('analyses.html', analyses=analyses)
        
    except Exception as e:
        logger.exception(f"Virhe analyysien listaamisessa: {e}")
        return jsonify({'error': f'Virhe analyysien listaamisessa: {str(e)}'}), 500

@app.route('/analysis/<int:analysis_id>')
@login_required
def view_analysis(analysis_id):
    """Näyttää yksittäisen tallennetun analyysin"""
    try:
        # Haetaan analyysi tietokannasta
        analysis = Analysis.query.get_or_404(analysis_id)
        
        # Tarkistetaan että käyttäjällä on oikeus nähdä tämä analyysi
        if analysis.user_id != current_user.id:
            flash('Sinulla ei ole oikeutta tähän analyysiin.', 'danger')
            return redirect(url_for('list_analyses'))
        
        # Haetaan kohteen tiedot kohteet-taulusta, jos ne ovat saatavilla
        kohde = Kohde.query.filter_by(analysis_id=analysis_id).first()
        osoite = kohde.osoite if kohde else None
        
        # Käytetään kohteen osoitetta otsikkona, jos se on saatavilla
        title = osoite or analysis.title or "Asuntoanalyysi"
        
        # Haetaan mahdollinen riskianalyysi
        risk_analysis = None
        try:
            risk_db = RiskAnalysis.query.filter_by(analysis_id=analysis_id).first()
            if risk_db and risk_db.risk_data:
                risk_analysis = json.loads(risk_db.risk_data)
                logger.info(f"Riskianalyysi löydetty analyysille {analysis_id}")
        except Exception as e:
            logger.error(f"Virhe riskianalyysin hakemisessa: {e}")
            
        return render_template('analysis.html', 
                               analysis=analysis, 
                               title=title,
                               kohde=kohde,
                               content=analysis.content,
                               risk_analysis=risk_analysis)
        
    except Exception as e:
        logger.exception(f"Virhe analyysin näyttämisessä: {e}")
        return jsonify({'error': f'Virhe analyysin näyttämisessä: {str(e)}'}), 500

@app.route('/analysis/raw/<int:analysis_id>')
@login_required
def download_analysis(analysis_id):
    """Lataa analyysin raakasisällön tekstitiedostona"""
    try:
        # Haetaan analyysi tietokannasta
        analysis = Analysis.query.get_or_404(analysis_id)
        
        # Tarkistetaan että käyttäjällä on oikeus ladata tämä analyysi
        if analysis.user_id != current_user.id:
            flash('Sinulla ei ole oikeutta tähän analyysiin.', 'danger')
            return redirect(url_for('list_analyses'))
        
        # Jos analysis.filename viittaa olemassa olevaan tiedostoon, ladataan se
        if analysis.filename and os.path.exists(os.path.join(api_call.ANALYSES_DIR, analysis.filename)):
            return send_from_directory(
                os.path.abspath(api_call.ANALYSES_DIR),
                analysis.filename,
                as_attachment=True,
                mimetype='text/plain'
            )
        
        # Muuten luodaan sisällöstä tiedosto ja palautetaan se
        response = jsonify({'content': analysis.content})
        response.headers.set('Content-Disposition', f'attachment; filename={analysis.filename or "analyysi.txt"}')
        response.headers.set('Content-Type', 'text/plain')
        return response
        
    except Exception as e:
        logger.exception(f"Virhe analyysin lataamisessa: {e}")
        return jsonify({'error': f'Virhe analyysin lataamisessa: {str(e)}'}), 500

@app.route('/upload-pdf', methods=['POST'])
@login_required
def upload_pdf():
    """Handle PDF uploads and process them using the same pipeline as Oikotie downloader"""
    try:
        # Check if the user is allowed to make API calls
        if not current_user.can_make_api_call():
            return render_template('error.html', 
                                error_title="API-kutsujen rajoitus", 
                                error_message="Olet käyttänyt kaikki API-kutsusi (2). Päivitä tilisi admin-tasoon jatkaaksesi käyttöä."), 403
        
        # Check if the post request has the file part
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'PDF-tiedosto puuttuu'}), 400
            
        pdf_file = request.files['pdf_file']
        
        # If user does not select file, browser also
        # submit an empty part without filename
        if pdf_file.filename == '':
            return jsonify({'error': 'PDF-tiedostoa ei valittu'}), 400
            
        if pdf_file:
            # Create a temporary file to save the uploaded PDF
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
                pdf_path = temp.name
                pdf_file.save(pdf_path)
                
            logger.info(f"PDF-tiedosto tallennettu väliaikaisesti: {pdf_path}")
            
            try:
                # Extract text from PDF using the same function as in oikotie_downloader
                logger.info("Puretaan tekstiä PDF-tiedostosta...")
                text_content = oikotie_downloader.extract_text_from_pdf(pdf_path)
                
                # Create property ID based on the file name and timestamp
                file_stem = os.path.splitext(pdf_file.filename)[0]
                property_id = f"{file_stem}_{int(time.time())}"
                
                # Format text into markdown
                logger.info("Muotoillaan teksti markdown-muotoon...")
                markdown_data = f"""# PDF-asuntoilmoitus

## Perustiedot
Lähde: Ladattu PDF
Tiedostonimi: {pdf_file.filename}
ID: {property_id}

## Ilmoituksen sisältö
{text_content}
"""
                
                # Haetaan kohteen perustiedot ensin KAT API:n avulla
                property_data = None
                kohde_id = None
                try:
                    logger.info("PDF: Haetaan kohteen perustiedot KAT API:lla")
                    property_data = kat_api_call.get_property_data(markdown_data)
                    
                    if property_data:
                        # Tallennetaan kohteet-tauluun ilman analysis_id:tä, liitetään myöhemmin
                        logger.info("PDF: Tallennetaan kohteen tiedot tietokantaan")
                        kohde_id = kat_api_call.save_property_data_to_db(property_data)
                        if kohde_id:
                            logger.info(f"PDF: Kohde tallennettu tietokantaan ID:llä {kohde_id}")
                        else:
                            logger.warning("PDF: Kohteen tallentaminen epäonnistui")
                    else:
                        logger.warning("PDF: Kohteen perustietoja ei saatu")
                except Exception as e:
                    logger.error(f"PDF: Virhe kohteen tietojen käsittelyssä: {e}")
                    logger.error(traceback.format_exc())
                
                # Use OpenAI API to analyze the data
                logger.info("Tehdään OpenAI API -kutsu analyysia varten")
                analysis_response = api_call.get_analysis(markdown_data, property_id)
                
                if not analysis_response:
                    logger.error("API-kutsu palautti tyhjän vastauksen")
                    return jsonify({'error': 'API-analyysi epäonnistui'}), 500
                    
                # Ensure the response is sanitized
                analysis_response = api_call.sanitize_markdown_response(analysis_response)
                
                # Sanitize content before template rendering
                sanitized_markdown = _sanitize_content(markdown_data)
                sanitized_analysis = _sanitize_content(analysis_response)
                
                # Increment API call count if user is not admin
                if not current_user.is_admin:
                    current_user.increment_api_call_count()
                
                # Get the analysis from database or create a new one
                analysis = Analysis.query.filter_by(property_url=property_id, user_id=current_user.id).first()
                analysis_id = None

                if analysis:
                    # Use existing analysis
                    analysis_id = analysis.id
                    logger.info(f"Käytetään olemassa olevaa analyysiä ID: {analysis_id}")
                else:
                    # This can happen because api_call.get_analysis saves the analysis to database
                    # Try to get the just created analysis by URL
                    analysis = Analysis.query.filter_by(property_url=property_id, user_id=current_user.id).first()
                    if analysis:
                        analysis_id = analysis.id
                        logger.info(f"Löydettiin juuri luotu analyysi ID: {analysis_id}")

                # Jos meillä on nyt kohde_id ja analysis_id, päivitetään kohteen analysis_id
                if kohde_id and analysis_id:
                    try:
                        logger.info(f"PDF: Päivitetään kohteen {kohde_id} analysis_id = {analysis_id}")
                        kohde = Kohde.query.get(kohde_id)
                        if kohde:
                            kohde.analysis_id = analysis_id
                            db.session.commit()
                            logger.info("PDF: Kohteen analysis_id päivitetty onnistuneesti")
                        else:
                            logger.warning(f"PDF: Kohdetta ID:llä {kohde_id} ei löytynyt")
                    except Exception as e:
                        logger.error(f"PDF: Virhe kohteen analysis_id:n päivittämisessä: {e}")
                        logger.error(traceback.format_exc())

                # Perform risk analysis from API response if analysis was found
                riski_data = None
                if analysis_id:
                    try:
                        logger.info("Tehdään riskianalyysi kohteesta")
                        riski_data_json = riskianalyysi(analysis_response, analysis_id)
                        logger.info(f"Saatiin riskianalyysin JSON vastaus pituudella: {len(riski_data_json)}")
                        riski_data = json.loads(riski_data_json)
                        logger.info(f"Riskianalyysi valmis: {riski_data.get('kokonaisriskitaso', 'N/A')}/10")
                    except Exception as e:
                        logger.error(f"Virhe riskianalyysissä: {e}")
                        logger.error(traceback.format_exc())
                
                # Remove the temporary file
                try:
                    os.remove(pdf_path)
                    logger.info("Tilapäinen PDF-tiedosto poistettu")
                except Exception as e:
                    logger.warning(f"Tilapäisen PDF-tiedoston poistaminen epäonnistui: {e}")
                
                # Redirect to the analysis page instead of rendering results
                if analysis_id:
                    return redirect(url_for('view_analysis', analysis_id=analysis_id))
                else:
                    # Render the results if we don't have an analysis ID for some reason
                    return render_template('results.html', 
                                    property_data=sanitized_markdown, 
                                    analysis=sanitized_analysis,
                                    riski_data=riski_data,
                                    property_url=property_id,
                                    analysis_id=analysis_id,
                                    source='pdf_upload')
                
            except Exception as e:
                logger.error(f"Virhe PDF:n käsittelyssä: {e}")
                logger.error(traceback.format_exc())
                
                # Clean up temporary file if it exists
                if os.path.exists(pdf_path):
                    try:
                        os.remove(pdf_path)
                    except:
                        pass
                
                return render_template('error.html', 
                                    error_title="Virhe PDF-tiedoston käsittelyssä", 
                                    error_message=f"PDF-tiedoston käsittelyssä tapahtui virhe: {str(e)}"), 500
    
    except Exception as e:
        logger.error(f"Virhe PDF-latauksessa: {e}")
        logger.error(traceback.format_exc())
        return render_template('error.html', 
                            error_title="Virhe PDF-latauksessa", 
                            error_message=f"PDF-tiedoston lataamisessa tapahtui virhe: {str(e)}"), 500

# Siirretään React-sovelluksen reitti juureen
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    """Tarjoaa React-sovelluksen"""
    # Jos polku on static-kansion alla, tarjoa tiedosto suoraan
    if path.startswith('static/'):
        # Pilko polku osiin ja siirrä static-kansion tiedosto
        path_parts = path.split('/', 1)
        if len(path_parts) > 1:
            return send_from_directory(os.path.join(app.root_path, path_parts[0]), path_parts[1])
        return app.send_static_file(path)
    
    # Jos on favicon tai muu Root-tason tiedosto
    if path in ['favicon.ico', 'manifest.json', 'logo192.png', 'logo512.png', 'robots.txt']:
        return send_from_directory(os.path.join(app.root_path, 'static', 'react'), path)
        
    # Tarkista onko polku joku API-reitti tai muu Flask-reitti
    if path.startswith('api/') or path.startswith('auth/') or path.startswith('flask/') or path.startswith('analyses/') or path.startswith('analysis/'):
        # Jos on API-kutsu, anna Flaskin hoitaa se normaalisti
        return app.send_static_file('react/index.html')
    
    # Tarkista onko pyydetty tiedosto olemassa static/react-kansiossa
    if path != "" and os.path.exists(os.path.join(app.root_path, 'static', 'react', path)):
        return send_from_directory(os.path.join(app.root_path, 'static', 'react'), path)
    
    # Muussa tapauksessa tarjoile index.html
    return send_from_directory(os.path.join(app.root_path, 'static', 'react'), 'index.html')

# JSON-API-reitti analyysien hakemiseen React-sovellukselle
@app.route('/api/analyses', methods=['GET'])
@login_required
def api_list_analyses():
    """Hakee käyttäjän analyysit JSON-muodossa React-sovellukselle"""
    analyses = Analysis.query.filter_by(user_id=current_user.id).order_by(Analysis.created_at.desc()).all()
    analyses_data = []
    
    for analysis in analyses:
        # Sanitoi sisältö
        sanitized_content = _sanitize_content(analysis.content)
        
        # Lisää analyysi listaan
        analyses_data.append({
            'id': analysis.id,
            'title': analysis.title,
            'content': sanitized_content,
            'created_at': analysis.created_at.strftime('%d.%m.%Y %H:%M'),
            'type': analysis.type
        })
    
    return jsonify({
        'status': 'success',
        'analyses': analyses_data
    })

# JSON-API-reitti yksittäisen analyysin hakemiseen React-sovellukselle
@app.route('/api/analysis/<int:analysis_id>', methods=['GET'])
@login_required
def api_view_analysis(analysis_id):
    """Hakee yksittäisen analyysin JSON-muodossa React-sovellukselle"""
    analysis = Analysis.query.get_or_404(analysis_id)
    
    # Tarkistetaan että käyttäjällä on oikeus nähdä analyysi
    if analysis.user_id != current_user.id:
        return jsonify({
            'status': 'error',
            'message': 'Sinulla ei ole oikeutta tähän analyysiin.'
        }), 403
    
    # Haetaan myös riskianalyysi jos se on olemassa
    risk_analysis = RiskAnalysis.query.filter_by(analysis_id=analysis.id).first()
    risk_analysis_data = None
    if risk_analysis:
        risk_analysis_data = {
            'id': risk_analysis.id,
            'content': risk_analysis.content,
            'created_at': risk_analysis.created_at.strftime('%d.%m.%Y %H:%M')
        }
    
    # Haetaan myös kohdetiedot jos ne ovat olemassa
    kohteet = Kohde.query.filter_by(analysis_id=analysis.id).all()
    kohteet_data = []
    for kohde in kohteet:
        kohteet_data.append({
            'id': kohde.id,
            'osoite': kohde.osoite,
            'tyyppi': kohde.tyyppi,
            'hinta': str(kohde.hinta) if kohde.hinta else None,
            'rakennusvuosi': kohde.rakennusvuosi
        })
    
    # Palauta analyysi
    return jsonify({
        'status': 'success',
        'analysis': {
            'id': analysis.id,
            'title': analysis.title,
            'content': _sanitize_content(analysis.content),
            'created_at': analysis.created_at.strftime('%d.%m.%Y %H:%M'),
            'type': analysis.type,
            'risk_analysis': risk_analysis_data,
            'kohteet': kohteet_data
        }
    })

if __name__ == '__main__':
    # Luodaan templates-kansio, jos sitä ei ole
    os.makedirs('templates', exist_ok=True)
    # Luodaan static/css ja static/js -kansiot, jos niitä ei ole
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    # Luodaan analyses-kansio, jos sitä ei ole
    os.makedirs('analyses', exist_ok=True)
    
    # Sovelluksen käynnistys
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port) 