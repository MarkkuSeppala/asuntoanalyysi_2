from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import logging
from real_estate_scraper import RealEstateScraper
import api_call
from flask_login import LoginManager, current_user, login_required
from models import db, User, Analysis, RiskAnalysis
from auth import auth
from config import get_config
from datetime import datetime
import sqlalchemy
from riskianalyysi import riskianalyysi
import json

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
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

# Lisätään päivämäärä kaikkiin templateihin
@app.context_processor
def inject_now():
    return {'now': datetime.now()}

@app.route('/welcome')
@login_required
def welcome():
    """Tervetulosivu kirjautuneille käyttäjille"""
    return render_template('welcome.html')

@app.route('/landing')
def landing():
    """Landing page - sovelluksen markkinointisivu"""
    return render_template('landing.html')

@app.route('/')
def index():
    """Etusivu, jossa käyttäjä voi syöttää asuntolinkin tai näkee landing-sivun"""
    if current_user.is_authenticated:
        return render_template('index.html')
    else:
        return render_template('landing.html')

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
        
        # Tarkistetaan, että URL on joko Oikotien tai Etuoven asunto-URL
        if 'oikotie.fi' not in url and 'asunnot.oikotie.fi' not in url and 'etuovi.com' not in url:
            return jsonify({'error': 'Syötä kelvollinen Oikotie- tai Etuovi-asuntolinkin URL'}), 400
        
        markdown_data = None
        success = False
        
        # Tarkistetaan onko kyseessä Etuovi-URL
        if 'etuovi.com' in url:
            logger.info(f"Käsitellään Etuovi URL: {url}")
            from etuovi_pipeline.etuovi_pipeline import process_etuovi_listing
            
            try:
                # Käytetään Etuovi-pipelinea markdownin luomiseen
                markdown_data = process_etuovi_listing(url)
                if markdown_data:
                    success = True
                    logger.info("Etuovi-kohteen tiedot haettu onnistuneesti")
                else:
                    logger.error("Etuovi-kohteen tietojen hakeminen epäonnistui - tyhjä tulos")
            except Exception as e:
                logger.exception(f"Virhe Etuovi-pipelinen käytössä: {e}")
                return jsonify({'error': f'Etuovi-kohteen tietojen hakeminen epäonnistui: {str(e)}'}), 500
        else:
            # Oikotie-URL:n käsittely
            logger.info(f"Haetaan tietoja Oikotie URL:sta: {url}")
            scraper = RealEstateScraper(url)
            success = scraper.run()
            
            if success:
                # Haetaan asunnon tiedot markdown-muodossa
                logger.info("Muunnetaan tiedot markdown-muotoon")
                markdown_data = scraper.format_to_markdown()
        
        if not success or not markdown_data:
            return jsonify({'error': 'Asunnon tietojen hakeminen epäonnistui'}), 500
        
        if not markdown_data:
            logger.error("Markdown-datan luominen epäonnistui - tyhjä tulos")
            return jsonify({'error': 'Markdown-muotoisen datan luominen epäonnistui'}), 500
        
        logger.debug(f"Markdown-datan pituus: {len(markdown_data)} merkkiä")
        
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

        # Tehdään riskianalyysi API-vastauksesta
        try:
            logger.info("Tehdään riskianalyysi kohteesta")
            riski_data_json = riskianalyysi(analysis_response, analysis_id)
            logger.info(f"Saatiin riskianalyysin JSON vastaus pituudella: {len(riski_data_json)}")
            riski_data = json.loads(riski_data_json)
            logger.info(f"Riskianalyysi valmis: {riski_data.get('kokonaisriskitaso', 'N/A')}/10")
        except Exception as e:
            logger.error(f"Virhe riskianalyysissä: {e}")
            riski_data = None
        
        logger.info("Renderöidään vastaussivu käyttäjälle")
        
        # Palautetaan sekä raakatiedot että analyysi
        return render_template('results.html', 
                            property_data=sanitized_markdown, 
                            analysis=sanitized_analysis,
                            riski_data=riski_data)
        
    except Exception as e:
        logger.exception(f"Odottamaton virhe analyysin teossa: {e}")
        return jsonify({'error': f'Virhe: {str(e)}'}), 500

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
        
        # Tarkistetaan, että URL on Oikotien tai Etuoven asunto-URL
        if 'oikotie.fi' not in url and 'asunnot.oikotie.fi' not in url and 'etuovi.com' not in url:
            return jsonify({'error': 'Syötä kelvollinen Oikotie- tai Etuovi-asuntolinkin URL'}), 400
        
        markdown_data = None
        success = False
        
        # Tarkistetaan onko kyseessä Etuovi-URL
        if 'etuovi.com' in url:
            logger.info(f"Käsitellään Etuovi URL: {url}")
            from etuovi_pipeline.etuovi_pipeline import process_etuovi_listing
            
            try:
                # Käytetään Etuovi-pipelinea markdownin luomiseen
                markdown_data = process_etuovi_listing(url)
                if markdown_data:
                    success = True
                    logger.info("Etuovi-kohteen tiedot haettu onnistuneesti")
                else:
                    logger.error("Etuovi-kohteen tietojen hakeminen epäonnistui - tyhjä tulos")
            except Exception as e:
                logger.exception(f"Virhe Etuovi-pipelinen käytössä: {e}")
                return jsonify({'error': f'Etuovi-kohteen tietojen hakeminen epäonnistui: {str(e)}'}), 500
        else:
            # Oikotie-URL:n käsittely
            logger.info(f"Haetaan tietoja Oikotie URL:sta: {url}")
            # Käytetään scraperia hakemaan asuntotiedot
            scraper = RealEstateScraper(url)
            success = scraper.run()
            
            if success:
                # Haetaan asunnon tiedot markdown-muodossa
                markdown_data = scraper.format_to_markdown()
        
        if not success or not markdown_data:
            return jsonify({'error': 'Asunnon tietojen hakeminen epäonnistui'}), 500
        
        if not markdown_data:
            return jsonify({'error': 'Markdown-muotoisen datan luominen epäonnistui'}), 500
        
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
            logger.info(f"Käytetään olemassa olevaa analyysiä ID: {analysis_id}")
            
            # Haetaan riskianalyysi jos sellainen on jo olemassa
            risk_analysis = RiskAnalysis.query.filter_by(analysis_id=analysis_id).first()
            if risk_analysis:
                riski_data = json.loads(risk_analysis.risk_data)
                logger.info(f"Käytetään olemassa olevaa riskianalyysiä")
        else:
            # Tätä voi tapahtua, koska api_call.get_analysis tallentaa analyysin tietokantaan
            # Yritetään hakea juuri luotu analyysi URL:n perusteella
            analysis = Analysis.query.filter_by(property_url=url, user_id=current_user.id).first()
            if analysis:
                analysis_id = analysis.id
                logger.info(f"Löydettiin juuri luotu analyysi ID: {analysis_id}")
        
        # Jos riskidataa ei ole vielä olemassa, luodaan se
        if not riski_data and analysis_id:
            try:
                logger.info("Tehdään riskianalyysi kohteesta")
                riski_data_json = riskianalyysi(analysis_response, analysis_id)
                riski_data = json.loads(riski_data_json)
                logger.info(f"Riskianalyysi valmis: {riski_data.get('kokonaisriskitaso', 'N/A')}/10")
            except Exception as e:
                logger.error(f"Virhe riskianalyysissä: {e}")
                # Ei palauteta virhettä käyttäjälle, jos riskianalyysi epäonnistuu
        
        # Kootaan API-vastaus
        response_data = {
            'status': 'success',
            'property_data': markdown_data,
            'analysis': analysis_response,
            'risk_analysis': riski_data
        }
        
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
                               title=analysis.title, 
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

@app.route('/api/demo-analyze', methods=['POST'])
def api_demo_analyze():
    """Rajoitettu API-pääte demokäyttöön, joka ottaa vastaan URL:n ja palauttaa analyysin JSON-muodossa"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL-osoite puuttuu'}), 400
        
        # Tarkistetaan, että URL on Oikotien tai Etuoven asunto-URL
        if 'oikotie.fi' not in url and 'asunnot.oikotie.fi' not in url and 'etuovi.com' not in url:
            return jsonify({'error': 'Syötä kelvollinen Oikotie- tai Etuovi-asuntolinkin URL'}), 400
        
        markdown_data = None
        success = False
        
        # Tarkistetaan onko kyseessä Etuovi-URL
        if 'etuovi.com' in url:
            logger.info(f"Käsitellään Etuovi URL: {url}")
            from etuovi_pipeline.etuovi_pipeline import process_etuovi_listing
            
            try:
                # Käytetään Etuovi-pipelinea markdownin luomiseen
                markdown_data = process_etuovi_listing(url)
                if markdown_data:
                    success = True
                    logger.info("Etuovi-kohteen tiedot haettu onnistuneesti")
                else:
                    logger.error("Etuovi-kohteen tietojen hakeminen epäonnistui - tyhjä tulos")
            except Exception as e:
                logger.exception(f"Virhe Etuovi-pipelinen käytössä: {e}")
                return jsonify({'error': f'Etuovi-kohteen tietojen hakeminen epäonnistui: {str(e)}'}), 500
        else:
            # Oikotie-URL:n käsittely
            logger.info(f"Haetaan tietoja Oikotie URL:sta: {url}")
            # Käytetään scraperia hakemaan asuntotiedot
            scraper = RealEstateScraper(url)
            success = scraper.run()
            
            if success:
                # Haetaan asunnon tiedot markdown-muodossa
                markdown_data = scraper.format_to_markdown()
        
        if not success or not markdown_data:
            return jsonify({'error': 'Asunnon tietojen hakeminen epäonnistui'}), 500
        
        if not markdown_data:
            return jsonify({'error': 'Markdown-muotoisen datan luominen epäonnistui'}), 500
        
        # Demo-versiossa palautetaan vain raakatiedot ilman API-analyysiä
        response_data = {
            'status': 'success',
            'property_data': markdown_data,
            'note': 'Demo-version rajoitettu vastaus. Täysi analyysi on saatavilla rekisteröityneille käyttäjille.'
        }
        
        return jsonify(response_data)
        
    except Exception as e:
        logger.exception(f"Odottamaton virhe demo-analyysissä: {e}")
        return jsonify({'error': f'Virhe: {str(e)}'}), 500

def _sanitize_content(content):
    """Sanitoi sisällön poistamalla Jinja2-templaten erikoismerkit."""
    if not content:
        return ""
    
    # Varmista että on merkkijono
    if not isinstance(content, str):
        content = str(content)
    
    # Escapeoi Jinja2-merkit
    content = content.replace("{{", "\\{{").replace("}}", "\\}}")
    content = content.replace("{%", "\\{%").replace("%}", "\\%}")
    content = content.replace("{#", "\\{#").replace("#}", "\\#}")
    
    return content

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