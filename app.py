import os
import logging
import json
import sys
import re
import traceback
import time
import tempfile
from functools import wraps
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, send_from_directory, redirect, url_for, flash, send_file, abort, session
from flask_login import LoginManager, current_user, login_required
import sqlalchemy
from sqlalchemy import text, exc
from flask_migrate import Migrate
import secrets
from flask_session import Session

import api_call
from models import db, User, Analysis, RiskAnalysis, Kohde, Product, Payment, Subscription
from auth import auth
from oauth import oauth_bp, init_google_blueprint  # Päivitetty import
from config import get_config
from riskianalyysi import riskianalyysi
import etuovi_downloader  # Import the etuovi_downloader
import oikotie_downloader  # Import the oikotie_downloader
import info_extract  # Käytetään info_extract-moduulia kat_api_call-moduulin kautta

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

# Lisää istuntoasetukset - TÄRKEÄÄ! OAuth vaatii toimivan istunnon
app.config['SESSION_TYPE'] = 'filesystem'  # Tallenna istunnot tiedostoihin
app.config['SESSION_PERMANENT'] = True  # Istunto säilyy vaikka selain suljetaan
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Istunnon kesto
app.config['SESSION_USE_SIGNER'] = True  # Allekirjoita evästeet
app.config['SESSION_KEY_PREFIX'] = 'kotiko_session:'  # Avainten etuliite

# Varmista että salaisuusavain on asetettu
if app.config.get('SECRET_KEY') is None or app.config.get('SECRET_KEY') == 'kehitys-avain-vaihda-tuotannossa':
    app.logger.warning("SECRET_KEY ei ole asetettu ympäristömuuttujissa! Generoidaan satunnainen avain.")
    app.config['SECRET_KEY'] = secrets.token_hex(32)

# Istunnon evästeasetukset - tärkeää OAuth:lle
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Ei salli JavaScriptin lukea evästettä
app.config['SESSION_COOKIE_SECURE'] = app.config.get('SESSION_COOKIE_SECURE', True)  # Vain HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Sallii redirectit

# Alusta Flask-Session
Session(app)

# Alustetaan tietokanta
db.init_app(app)

# Alustetaan migraatiot
migrate = Migrate(app, db)

# Alustetaan kirjautumisenhallinta
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Kirjaudu sisään käyttääksesi tätä sivua.'
login_manager.login_message_category = 'info'

# Lisätään tietokantayhteyden virheiden käsittely
def retry_on_db_error(max_retries=3, retry_delay=1):
    """Decorator, joka yrittää suorittaa tietokantaoperaation uudelleen virhetilanteissa"""
    def decorator(f):
        @wraps(f)
        def wrapped_f(*args, **kwargs):
            attempts = 0
            while attempts < max_retries:
                try:
                    return f(*args, **kwargs)
                except (exc.OperationalError, exc.ProgrammingError, exc.DisconnectionError) as e:
                    attempts += 1
                    app.logger.warning(f"Tietokantavirhe (yritys {attempts}/{max_retries}): {str(e)}")
                    
                    # Jos viimeinen yritys, nosta virhe uudelleen
                    if attempts >= max_retries:
                        app.logger.error(f"Kaikki yritykset epäonnistuivat: {str(e)}")
                        raise
                    
                    # Sulje päättyneeksi merkitty yhteys ja odota ennen uutta yritystä
                    try:
                        db.session.rollback()
                    except:
                        pass
                    
                    # Odota ennen uudelleenyritystä (exponentiaalinen backoff)
                    sleep_time = retry_delay * (2 ** (attempts - 1))
                    app.logger.info(f"Odotetaan {sleep_time}s ennen uudelleenyritystä...")
                    time.sleep(sleep_time)
            return None  # Ei pitäisi koskaan päästä tänne
        return wrapped_f
    return decorator

# Sovelletaan tietokantayhteyden virheiden käsittelyä load_user-funktioon
@login_manager.user_loader
@retry_on_db_error(max_retries=3)
def load_user(user_id):
    """Lataa käyttäjä session tunnisteen perusteella"""
    return User.query.get(int(user_id))

# Rekisteröidään blueprint-komponentit
app.register_blueprint(auth, url_prefix='/auth')
app.register_blueprint(oauth_bp, url_prefix='/oauth')
init_google_blueprint(app)  # Alustetaan Google OAuth blueprint

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
    
    # Päivitetään kohteet-taulun rakenne tarvittaessa
    try:
        # Tarkistetaan onko risk_level-sarake jo olemassa
        kohteet_columns = [c['name'] for c in inspector.get_columns('kohteet')] if 'kohteet' in tables else []
        if 'risk_level' not in kohteet_columns and 'kohteet' in tables:
            logger.info("Lisätään risk_level-sarake kohteet-tauluun...")
            with db.engine.connect() as conn:
                with conn.begin():
                    conn.execute(text("""
                    ALTER TABLE kohteet 
                    ADD COLUMN risk_level NUMERIC(3,1)
                    """))
            logger.info("risk_level-sarake lisätty onnistuneesti!")
    except Exception as e:
        logger.error(f"Virhe risk_level-sarakkeen lisäämisessä: {e}")

# Lisätään päivämäärä kaikkiin templateihin
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/landing')
def landing():
    """Landing page - sovelluksen markkinointisivu"""
    return render_template('landing.html')

@app.route('/products')
def products():
    """Tuotteet - sivusto tuotevaihtoehtoineen"""
    return render_template('products.html')

@app.route('/')
def index():
    """Etusivu, jossa käyttäjä voi syöttää asuntolinkin tai näkee landing-sivun"""
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
    """Analysointi-reitti, joka ottaa vastaan URL:n ja palauttaa analyysin"""
    try:
        # Luodaan sessio ID jokaiselle analyysi-pyynnölle
        import uuid
        session_id = str(uuid.uuid4())
        logger.info(f"Aloitetaan analyysi käyttäjälle {current_user.id}, sessio {session_id}")
        
        # Tarkista käyttäjän oikeus tehdä analyysi
        if not current_user.can_make_api_call():
            flash('Sinulla ei ole oikeutta tehdä enempää analyysejä. Hanki lisää analyysejä ostamalla paketti.', 'danger')
            return redirect(url_for('products'))
            
        url = request.form.get('url')
        
        if not url:
            flash('URL-osoite on pakollinen', 'danger')
            return redirect(url_for('index'))
        
        # Tarkistetaan, että URL on hyväksytty URL (Oikotie tai Etuovi)
        if ('oikotie.fi' not in url and 'asunnot.oikotie.fi' not in url and 
            'etuovi.com' not in url):
            flash('Syötä kelvollinen Oikotie- tai Etuovi-asuntolinkin URL', 'danger')
            return redirect(url_for('index'))
        
        # Haetaan asunnon tiedot URL:n perusteella
        logger.info(f"Haetaan tietoja URL:sta: {url}")
        success, markdown_data, source = get_property_data(url)
        
        if not success or not markdown_data:
            logger.error("Asuntoilmoituksen noutaminen epäonnistui")
            flash("Ilmoituksen hakemisessa tapahtui virhe. Ole hyvä, yritä myöhemmin uudelleen.", 'danger')
            return redirect(url_for('index'))
        
        # Haetaan kohteen perustiedot ensin KAT API:n avulla
        property_data = None
        kohde_id = None
        kohde_tyyppi = None
        try:
            logger.info("Haetaan kohteen perustiedot KAT API:lla")
            property_data_json = info_extract.get_property_data(markdown_data)
            
            if property_data_json:
                # Muunnetaan JSON-merkkijono sanakirjaksi
                try:
                    property_data = json.loads(property_data_json)
                    logger.info("JSON-merkkijono muunnettu sanakirjaksi onnistuneesti")
                except json.JSONDecodeError as e:
                    logger.error(f"Virhe JSON-merkkijonon muuntamisessa sanakirjaksi: {e}")
                    property_data = None
                
                # Tallennetaan kohteet-tauluun ilman analysis_id:tä, liitetään myöhemmin
                logger.info("Tallennetaan kohteen tiedot tietokantaan")
                
                # Varmistetaan että kohde tallennetaan käyttäjäkohtaisesti
                logger.info(f"Kohde tallennetaan käyttäjälle {current_user.id}, sessio {session_id}")
                kohde_id = info_extract.save_property_data_to_db(property_data, user_id=current_user.id)
                
                if kohde_id:
                    logger.info(f"Kohde tallennettu tietokantaan ID:llä {kohde_id}")
                    # Haetaan kohteen tyyppi
                    kohde = Kohde.query.get(kohde_id)
                    if kohde and kohde.tyyppi:
                        kohde_tyyppi = kohde.tyyppi
                        logger.info(f"Kohteen tyyppi: {kohde_tyyppi}")
                    
                    # Linkitetään kohde käyttäjään manuaalisesti päivittämällä kohteen tiedot
                    try:
                        if kohde:
                            # Varmistetaan että kohde on sidottu käyttäjään päivittämällä analysis myöhemmin
                            logger.info(f"Kohde {kohde_id} merkitty käyttäjälle {current_user.id}")
                    except Exception as e:
                        logger.error(f"Virhe kohteen käyttäjäsidonnaisuuden päivityksessä: {e}")
                else:
                    logger.warning("Kohteen tallentaminen epäonnistui")
            else:
                logger.warning("Kohteen perustietoja ei saatu")
        except Exception as e:
            logger.error(f"Virhe kohteen tietojen käsittelyssä: {e}")
        
        # Tarkistetaan, onko kohde jo analysoitu tällä käyttäjällä
        existing_analysis = None
        try:
            existing_analysis = Analysis.query.filter_by(
                property_url=url, 
                user_id=current_user.id
            ).first()
            
            if existing_analysis:
                logger.info(f"Käyttäjällä {current_user.id} on jo analyysi tälle URL:lle: {existing_analysis.id}")
                
                # Tarkistetaan onko analyysi tuore (alle 7 päivää vanha)
                if existing_analysis.created_at > datetime.utcnow() - timedelta(days=7):
                    logger.info(f"Käytetään olemassa olevaa analyysiä {existing_analysis.id} (alle 7 päivää vanha)")
                    
                    analysis_response = existing_analysis.content
                    saved_file = existing_analysis.filename
                    analysis_id = existing_analysis.id
                    
                    # Haetaan olemassa oleva riskianalyysi
                    riski_data = None
                    try:
                        risk_db = RiskAnalysis.query.filter_by(
                            analysis_id=analysis_id, 
                            user_id=current_user.id
                        ).first()
                        
                        if risk_db and risk_db.risk_data:
                            riski_data = json.loads(risk_db.risk_data)
                            logger.info(f"Käytetään olemassa olevaa riskianalyysiä analyysille {analysis_id}")
                        else:
                            # Jos riskianalyysiä ei löydy, tehdään se nyt
                            logger.info(f"Olemassa olevalle analyysille ei löydy riskianalyysiä, tehdään se nyt")
                            riski_data_json = riskianalyysi(analysis_response, analysis_id, current_user.id)
                            if riski_data_json:
                                riski_data = json.loads(riski_data_json)
                    except Exception as e:
                        logger.error(f"Virhe riskianalyysin hakemisessa: {e}")
                    
                    # Ohjataan käyttäjä suoraan analyysin sivulle
                    return redirect(url_for('view_analysis', analysis_id=analysis_id))
        except Exception as e:
            logger.error(f"Virhe tarkistettaessa olemassa olevia analyysejä: {e}")
        
        # Käytetään OpenAI API:a analyysin tekemiseen
        logger.info(f"Tehdään OpenAI API -kutsu analyysia varten käyttäjälle {current_user.id}, sessio {session_id}")
        analysis_response, saved_file, db_analysis_id = api_call.get_analysis(markdown_data, url, kohde_tyyppi, current_user.id)
        
        if not analysis_response:
            logger.error("API-kutsu palautti tyhjän vastauksen")
            flash("Analyysin muodostamisessa tapahtui virhe. Ole hyvä, yritä myöhemmin uudelleen.", 'danger')
            return redirect(url_for('index'))
            
        # Varmistetaan että vastaus on puhdistettu (API:ssa puhdistus tehdään jo, tämä on varmuuden vuoksi)
        analysis_response = api_call.sanitize_markdown_response(analysis_response)
        
        # Käytetään suoraan API:n palauttamaa analysis_id:tä jos se on saatavilla
        analysis_id = db_analysis_id
        
        # Jos analysis_id ei ole saatavilla, yritetään hakea se tietokannasta
        if not analysis_id:
            # Haetaan analyysi tietokannasta URL:n perusteella
            analysis = Analysis.query.filter_by(property_url=url, user_id=current_user.id).first()
            if analysis:
                analysis_id = analysis.id
                logger.info(f"Käytetään olemassa olevaa analyysiä ID: {analysis_id}")
        
        # Jos meillä on nyt kohde_id ja analysis_id, päivitetään kohteen analysis_id
        if kohde_id and analysis_id:
            try:
                logger.info(f"Päivitetään kohteen {kohde_id} analysis_id = {analysis_id}")
                kohde = Kohde.query.get(kohde_id)
                if kohde:
                    kohde.analysis_id = analysis_id
                    
                    # Varmistetaan että kohde on sidottu käyttäjään
                    if not kohde.user_id:
                        kohde.user_id = current_user.id
                        
                    db.session.commit()
                    logger.info("Kohteen analysis_id päivitetty onnistuneesti")
                else:
                    logger.warning(f"Kohdetta ID:llä {kohde_id} ei löytynyt")
            except Exception as e:
                logger.error(f"Virhe kohteen analysis_id:n päivittämisessä: {e}")
                # Session rollback virheen sattuessa
                db.session.rollback()
        
        # Tehdään riskianalyysi API-vastauksesta, jos analyysi on löydetty
        riski_data = None
        if analysis_id:
            try:
                logger.info(f"Tehdään riskianalyysi kohteesta, analyysi {analysis_id}, käyttäjä {current_user.id}")
                riski_data_json = riskianalyysi(analysis_response, analysis_id, current_user.id)
                logger.info(f"Saatiin riskianalyysin JSON vastaus pituudella: {len(riski_data_json)}")
                riski_data = json.loads(riski_data_json)
                logger.info(f"Riskianalyysi valmis: {riski_data.get('kokonaisriskitaso', 'N/A')}/10")
            except Exception as e:
                logger.error(f"Virhe riskianalyysissä: {e}")
                logger.error(traceback.format_exc())
        
        # Jos käyttäjällä ei ole kuukausijäsenyyttä, vähennä jäljellä olevia analyysejä
        active_subscription = Subscription.query.filter_by(
            user_id=current_user.id, 
            status='active',
            subscription_type='monthly'
        ).first()
        
        if not current_user.is_admin and not active_subscription:
            logger.info(f"Vähennetään yksi analyysi käyttäjältä {current_user.id}. Analyysejä jäljellä ennen vähennystä: {current_user.analyses_left}")
            current_user.decrement_analyses_left()
            logger.info(f"Analyysejä jäljellä vähennyksen jälkeen: {current_user.analyses_left}")
        
        # Ohjataan käyttäjä analyysin sivulle sen sijaan että renderöidään results.html
        logger.info(f"Analyysi valmis käyttäjälle {current_user.id}, sessio {session_id}")
        
        if analysis_id:
            return redirect(url_for('view_analysis', analysis_id=analysis_id))
        else:
            # Jos jostain syystä analysis_id ei ole saatavilla, renderöidään results.html
            # Sanitoidaan sisältö ennen template-renderöintiä
            sanitized_markdown = _sanitize_content(markdown_data)
            sanitized_analysis = _sanitize_content(analysis_response)
            
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
                'message': 'Sinulla ei ole oikeutta tehdä enempää analyysejä. Hanki lisää analyysejä ostamalla paketti.'
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
        kohde_tyyppi = None
        try:
            logger.info("API: Haetaan kohteen perustiedot KAT API:lla")
            property_data_json = info_extract.get_property_data(markdown_data)
            
            if property_data_json:
                # Muunnetaan JSON-merkkijono sanakirjaksi
                try:
                    property_data = json.loads(property_data_json)
                    logger.info("JSON-merkkijono muunnettu sanakirjaksi onnistuneesti")
                except json.JSONDecodeError as e:
                    logger.error(f"Virhe JSON-merkkijonon muuntamisessa sanakirjaksi: {e}")
                    property_data = None
                
                # Tallennetaan kohteet-tauluun ilman analysis_id:tä, liitetään myöhemmin
                logger.info("API: Tallennetaan kohteen tiedot tietokantaan")
                kohde_id = info_extract.save_property_data_to_db(property_data, user_id=current_user.id)
                if kohde_id:
                    logger.info(f"API: Kohde tallennettu tietokantaan ID:llä {kohde_id}")
                    # Haetaan kohteen tyyppi
                    kohde = Kohde.query.get(kohde_id)
                    if kohde and kohde.tyyppi:
                        kohde_tyyppi = kohde.tyyppi
                        logger.info(f"API: Kohteen tyyppi: {kohde_tyyppi}")
                else:
                    logger.warning("API: Kohteen tallentaminen epäonnistui")
            else:
                logger.warning("API: Kohteen perustietoja ei saatu")
        except Exception as e:
            logger.error(f"API: Virhe kohteen tietojen käsittelyssä: {e}")
        
        # Käytetään OpenAI API:a analyysin tekemiseen
        logger.info("Tehdään OpenAI API -kutsu analyysia varten")
        analysis_response, saved_file, db_analysis_id = api_call.get_analysis(markdown_data, url, kohde_tyyppi, current_user.id)
        
        if not analysis_response:
            logger.error("API-kutsu palautti tyhjän vastauksen")
            return jsonify({'error': 'API-analyysi epäonnistui'}), 500
            
        # Varmistetaan että vastaus on puhdistettu (API:ssa puhdistus tehdään jo)
        analysis_response = api_call.sanitize_markdown_response(analysis_response)
        
        # Jos käyttäjällä ei ole kuukausijäsenyyttä, vähennä jäljellä olevia analyysejä
        active_subscription = Subscription.query.filter_by(
            user_id=current_user.id, 
            status='active',
            subscription_type='monthly'
        ).first()
        
        if not current_user.is_admin and not active_subscription:
            logger.info(f"API: Vähennetään yksi analyysi käyttäjältä {current_user.id}. Analyysejä jäljellä ennen vähennystä: {current_user.analyses_left}")
            current_user.decrement_analyses_left()
            logger.info(f"API: Analyysejä jäljellä vähennyksen jälkeen: {current_user.analyses_left}")
        
        # Käytetään suoraan API:n palauttamaa analysis_id:tä jos se on saatavilla
        analysis_id = db_analysis_id
        
        # Jos analysis_id ei ole saatavilla, yritetään hakea se tietokannasta
        if not analysis_id:
            # Haetaan analyysi tietokannasta URL:n perusteella
            analysis = Analysis.query.filter_by(property_url=url, user_id=current_user.id).first()
            if analysis:
                analysis_id = analysis.id
                logger.info(f"Käytetään olemassa olevaa analyysiä ID: {analysis_id}")
        
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
                logger.info("API: Tehdään riskianalyysi kohteesta")
                riski_data_json = riskianalyysi(analysis_response, analysis_id, current_user.id)
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
        
        # Lisätään analyysin ID vastaukseen, jos se on saatavilla
        if analysis_id:
            response_data['analysis_id'] = analysis_id
        
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
        logger.info(f"Analyysi {analysis_id} haettu käyttäjälle {current_user.id}, otsikko: {analysis.title}")
        
        # Tarkistetaan että käyttäjällä on oikeus nähdä tämä analyysi
        if analysis.user_id != current_user.id:
            logger.warning(f"Käyttäjä {current_user.id} yritti katsoa analyysiä {analysis_id}, joka kuuluu käyttäjälle {analysis.user_id}")
            flash('Sinulla ei ole oikeutta tähän analyysiin.', 'danger')
            return redirect(url_for('list_analyses'))
        
        # Haetaan kohteen tiedot kohteet-taulusta, jos ne ovat saatavilla
        kohde = Kohde.query.filter_by(analysis_id=analysis_id).first()
        
        if kohde:
            logger.info(f"Kohde löytyi analyysille {analysis_id}: ID={kohde.id}, osoite={kohde.osoite}, tyyppi={kohde.tyyppi}")
            # Käytetään user_id-kenttää tarkistamaan onko kohde sidottu käyttäjään
            if kohde.user_id and kohde.user_id != current_user.id:
                logger.warning(f"Kohde {kohde.id} ei kuulu käyttäjälle {current_user.id}, vaan käyttäjälle {kohde.user_id}")
        else:
            logger.warning(f"Kohdetta ei löytynyt analyysille {analysis_id}")
        
        osoite = kohde.osoite if kohde and kohde.osoite else None
        
        if not osoite or osoite == "Tuntematon":
            logger.warning(f"Analyysille {analysis_id} ei löytynyt kelvollista osoitetta")
            # Yritetään löytää osoite analyysin sisällöstä
            if kohde and not kohde.osoite and analysis.content:
                # Etsitään osoitetta analyysin sisällöstä ensimmäiseltä riviltä
                first_line = analysis.content.strip().split('\n')[0] if '\n' in analysis.content else analysis.content
                if first_line and len(first_line) < 100:  # Varmistetaan että ensimmäinen rivi on järkevä
                    logger.info(f"Yritetään päivittää osoitetietoa analyysin sisällöstä: '{first_line}'")
                    kohde.osoite = first_line
                    try:
                        db.session.commit()
                        osoite = first_line
                        logger.info(f"Päivitettiin osoite kohteelle {kohde.id}: {osoite}")
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Virhe osoitteen päivittämisessä: {e}")
        
        # Käytetään kohteen osoitetta otsikkona, jos se on saatavilla
        title = osoite or analysis.title or "Asuntoanalyysi"
        logger.info(f"Käytetään otsikkoa: {title}")
        
        # Haetaan mahdollinen riskianalyysi
        risk_analysis = None
        try:
            risk_db = RiskAnalysis.query.filter_by(analysis_id=analysis_id).first()
            if risk_db and risk_db.risk_data:
                risk_analysis = json.loads(risk_db.risk_data)
                logger.info(f"Riskianalyysi löydetty analyysille {analysis_id}")
            else:
                logger.warning(f"Riskianalyysiä ei löytynyt analyysille {analysis_id}")
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
    """Handle PDF uploads and process them using info_extract to extract data"""
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
                # Create property ID based on the file name and timestamp
                file_stem = os.path.splitext(pdf_file.filename)[0]
                property_id = f"{file_stem}_{int(time.time())}"
                
                # Suorita PDF-tiedoston tietojen poiminta käyttäen info_extract-moduulia
                logger.info("Poimitaan tietoja PDF-tiedostosta info_extract-moduulilla...")
                extracted_data = info_extract.process_single_pdf(
                    pdf_path=pdf_path, 
                    kaupunki_nimi="PDF-lataus",
                    user_id=current_user.id
                )
                
                # Tarkistetaan saatiinko kohde_id suoraan process_single_pdf-funktiosta
                kohde_id = None
                kohde_tyyppi = None
                
                if extracted_data and extracted_data.get("kohde_id"):
                    kohde_id = extracted_data.get("kohde_id")
                    logger.info(f"PDF: Kohde tallennettu tietokantaan ID:llä {kohde_id}")
                    
                    # Haetaan kohteen tyyppi
                    kohde = Kohde.query.get(kohde_id)
                    if kohde and kohde.tyyppi:
                        kohde_tyyppi = kohde.tyyppi
                        logger.info(f"PDF: Kohteen tyyppi: {kohde_tyyppi}")
                else:
                    logger.warning("PDF: Tietojen poiminta tai tallennus suoralla metodilla epäonnistui, yritetään vaihtoehtoista tapaa")
                    
                    # Jos suora poiminta epäonnistui, yritetään vaihtoehtoista tapaa
                    # Extract text from PDF for API analysis
                    text_content = oikotie_downloader.extract_text_from_pdf(pdf_path)
                    
                    # Format text into markdown for analysis
                    markdown_data = f"""# PDF-asuntoilmoitus

## Perustiedot
Lähde: Ladattu PDF
Tiedostonimi: {pdf_file.filename}
ID: {property_id}

## Ilmoituksen sisältö
{text_content}
"""
                    
                    # Haetaan kohteen perustiedot API:lla
                    try:
                        logger.info("PDF: Haetaan kohteen perustiedot API:lla")
                        property_data_json = info_extract.get_property_data(markdown_data)
                        
                        if property_data_json:
                            # Muunnetaan JSON-merkkijono sanakirjaksi
                            try:
                                property_data = json.loads(property_data_json)
                                logger.info("PDF: JSON-merkkijono muunnettu sanakirjaksi onnistuneesti")
                            except json.JSONDecodeError as e:
                                logger.error(f"PDF: Virhe JSON-merkkijonon muuntamisessa sanakirjaksi: {e}")
                                property_data = None
                            
                            # Tallenna tiedot tietokantaan jos ne ovat saatavilla
                            if property_data:
                                logger.info("PDF: Tallennetaan kohteen tiedot tietokantaan")
                                kohde_id = info_extract.save_property_data_to_db(property_data, user_id=current_user.id)
                                if kohde_id:
                                    logger.info(f"PDF: Kohde tallennettu tietokantaan ID:llä {kohde_id}")
                                    # Haetaan kohteen tyyppi
                                    kohde = Kohde.query.get(kohde_id)
                                    if kohde and kohde.tyyppi:
                                        kohde_tyyppi = kohde.tyyppi
                                        logger.info(f"PDF: Kohteen tyyppi: {kohde_tyyppi}")
                                else:
                                    logger.warning("PDF: Kohteen tallentaminen tietokantaan epäonnistui")
                            else:
                                logger.warning("PDF: Kohteen tietojen muuntaminen sanakirjaksi epäonnistui")
                        else:
                            logger.warning("PDF: Kohteen perustietoja ei saatu API:sta")
                    except Exception as e:
                        logger.error(f"PDF: Virhe kohteen tietojen käsittelyssä: {e}")
                        logger.error(traceback.format_exc())
                
                # Käytetään samaa markdown_data-muuttujaa OpenAI API:n kutsuun
                if 'markdown_data' not in locals():
                    # Jos markdown_data ei ole vielä määritelty, määritellään se nyt
                    text_content = oikotie_downloader.extract_text_from_pdf(pdf_path)
                    markdown_data = f"""# PDF-asuntoilmoitus

## Perustiedot
Lähde: Ladattu PDF
Tiedostonimi: {pdf_file.filename}
ID: {property_id}

## Ilmoituksen sisältö
{text_content}
"""
                
                # Use OpenAI API to analyze the data
                logger.info("Tehdään OpenAI API -kutsu analyysia varten")
                analysis_response, saved_file, db_analysis_id = api_call.get_analysis(markdown_data, property_id, kohde_tyyppi, current_user.id)
                
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
                    current_user.increment_api_calls()
                
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
                        riski_data_json = riskianalyysi(analysis_response, analysis_id, current_user.id)
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

# Maksujärjestelmän reitit
@app.route('/checkout/<int:product_id>', methods=['GET'])
@login_required
def checkout(product_id):
    """Näyttää maksusivun valitulle tuotteelle"""
    try:
        # Haetaan tuote tietokannasta
        product = Product.query.get_or_404(product_id)
        
        if not product.active:
            flash('Tuote ei ole enää saatavilla.', 'danger')
            return redirect(url_for('products'))
            
        return render_template('checkout.html', product=product)
        
    except Exception as e:
        logger.exception(f"Virhe maksusivun näyttämisessä: {e}")
        flash('Maksusivun lataamisessa tapahtui virhe. Yritä uudelleen.', 'danger')
        return redirect(url_for('products'))

@app.route('/process_payment/<int:product_id>', methods=['POST'])
@login_required
def process_payment(product_id):
    """Käsittelee maksun. Tämä on yksinkertaistettu versio ilman oikeaa maksukäsittelijää."""
    try:
        # Haetaan tuote tietokannasta
        product = Product.query.get_or_404(product_id)
        
        if not product.active:
            flash('Tuote ei ole enää saatavilla.', 'danger')
            return redirect(url_for('products'))
            
        # Tämä on demo-versio ilman oikeaa maksukäsittelijää
        # Oikeassa toteutuksessa tässä olisi integraatio maksunvälittäjään (esim. Stripe, PayPal, jne.)
        
        # Luodaan maksu
        payment = Payment(
            user_id=current_user.id,
            product_id=product.id,
            amount=product.price,
            payment_method='demo',
            transaction_id=f'demo_{int(datetime.utcnow().timestamp())}',
            status='completed'
        )
        
        db.session.add(payment)
        
        # Jos kyseessä on kertaostos
        if product.product_type == 'one_time':
            # Lisätään käyttäjälle analyysejä
            current_user.add_analyses(product.analyses_count)
            flash(f'Ostoksesi on käsitelty onnistuneesti! {product.analyses_count} analyysiä on lisätty tilillesi.', 'success')
            
        # Jos kyseessä on kuukausitilaus
        elif product.product_type == 'subscription':
            # Luodaan uusi tilaus
            from datetime import timedelta
            
            subscription = Subscription(
                user_id=current_user.id,
                product_id=product.id,
                subscription_type='monthly',
                status='active',
                expires_at=datetime.utcnow() + timedelta(days=30),
                next_billing_date=datetime.utcnow() + timedelta(days=30),
                last_payment_date=datetime.utcnow(),
                payment_id=payment.transaction_id
            )
            
            db.session.add(subscription)
            
            # Päivitetään maksun subscription_id
            payment.subscription_id = subscription.id
            
            flash('Tilauksesi on aktivoitu onnistuneesti! Voit nyt tehdä rajattomasti analyysejä.', 'success')
        
        db.session.commit()
        
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.exception(f"Virhe maksun käsittelyssä: {e}")
        db.session.rollback()
        flash('Maksun käsittelyssä tapahtui virhe. Yritä uudelleen.', 'danger')
        return redirect(url_for('checkout', product_id=product_id))

@app.route('/my_subscription')
@login_required
def my_subscription():
    """Näyttää käyttäjän tilaustiedot"""
    try:
        # Haetaan käyttäjän aktiivinen tilaus
        subscription = Subscription.query.filter_by(
            user_id=current_user.id,
            status='active'
        ).first()
        
        # Haetaan käyttäjän maksut
        payments = Payment.query.filter_by(
            user_id=current_user.id,
            status='completed'
        ).order_by(Payment.created_at.desc()).all()
        
        # Haetaan tuotevalikoima
        products = Product.query.filter_by(active=True).all()
        
        return render_template('my_subscription.html', 
                              subscription=subscription,
                              payments=payments,
                              products=products,
                              analyses_left=current_user.analyses_left)
        
    except Exception as e:
        logger.exception(f"Virhe tilaustietojen näyttämisessä: {e}")
        flash('Tilaustietojen lataamisessa tapahtui virhe. Yritä uudelleen.', 'danger')
        return redirect(url_for('index'))

@app.route('/cancel_subscription/<int:subscription_id>', methods=['POST'])
@login_required
def cancel_subscription(subscription_id):
    """Peruuttaa käyttäjän tilauksen"""
    try:
        # Haetaan tilaus tietokannasta
        subscription = Subscription.query.get_or_404(subscription_id)
        
        # Tarkistetaan että käyttäjällä on oikeus peruuttaa tämä tilaus
        if subscription.user_id != current_user.id:
            flash('Sinulla ei ole oikeutta peruuttaa tätä tilausta.', 'danger')
            return redirect(url_for('my_subscription'))
            
        # Peruutetaan tilaus 
        cancel_immediately = request.form.get('cancel_immediately') == 'true'
        subscription.cancel(immediate=cancel_immediately)
        
        if cancel_immediately:
            flash('Tilauksesi on peruutettu välittömästi.', 'success')
        else:
            flash('Tilauksesi on merkitty peruutettavaksi nykyisen laskutuskauden lopussa.', 'success')
            
        return redirect(url_for('my_subscription'))
        
    except Exception as e:
        logger.exception(f"Virhe tilauksen peruuttamisessa: {e}")
        flash('Tilauksen peruuttamisessa tapahtui virhe. Yritä uudelleen.', 'danger')
        return redirect(url_for('my_subscription'))

# Lisätään diagnostiikkareitit kehitysympäristöön
@app.route('/debug/session')
def debug_session():
    """Näyttää istunnon sisällön - KÄYTÄ VAIN KEHITYSYMPÄRISTÖSSÄ"""
    if app.config.get('FLASK_ENV') != 'development':
        return jsonify({"error": "Tämä reitti on saatavilla vain kehitysympäristössä"}), 403
        
    # Tarkista onko käyttäjä kirjautunut
    is_logged_in = current_user.is_authenticated
    user_info = {
        "id": current_user.id,
        "email": current_user.email,
        "name": f"{current_user.first_name} {current_user.last_name}"
    } if is_logged_in else None
    
    # Kerää istuntotiedot
    session_data = {}
    for key in session:
        # Älä näytä arkaluontoista tietoa
        if key in ['_google_oauth_token', 'csrf_token', '_csrf_token']:
            session_data[key] = "***SENSUROITU***"
        else:
            session_data[key] = session[key]
    
    # Kerää evästetiedot
    cookie_data = {}
    for key, value in request.cookies.items():
        if 'session' in key.lower() or 'token' in key.lower():
            cookie_data[key] = "***SENSUROITU***"
        else:
            cookie_data[key] = value
    
    # Palauta diagnostiikkatiedot
    return jsonify({
        "is_logged_in": is_logged_in,
        "user": user_info,
        "session": session_data,
        "cookies": cookie_data,
        "config": {
            "session_type": app.config.get('SESSION_TYPE'),
            "session_permanent": app.config.get('SESSION_PERMANENT'),
            "session_cookie_secure": app.config.get('SESSION_COOKIE_SECURE'),
            "session_cookie_httponly": app.config.get('SESSION_COOKIE_HTTPONLY'),
            "session_cookie_samesite": app.config.get('SESSION_COOKIE_SAMESITE')
        },
        "oauth": {
            "google_authorized": hasattr(google, 'authorized') and google.authorized
        }
    })

@app.route('/debug/clear-session')
def debug_clear_session():
    """Tyhjentää istunnon - KÄYTÄ VAIN KEHITYSYMPÄRISTÖSSÄ"""
    if app.config.get('FLASK_ENV') != 'development':
        return jsonify({"error": "Tämä reitti on saatavilla vain kehitysympäristössä"}), 403
    
    # Tyhjennä istunto
    session.clear()
    
    return jsonify({
        "success": True,
        "message": "Istunto tyhjennetty onnistuneesti"
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