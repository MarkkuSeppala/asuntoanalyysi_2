from flask import Flask, render_template, request, jsonify, send_from_directory
import os
import logging
from real_estate_scraper import RealEstateScraper
import api_call

# Asetetaan lokitus
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route('/')
def index():
    """Etusivu, jossa käyttäjä voi syöttää asuntolinkin"""
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """Käsittelee käyttäjän syöttämän URL:n ja palauttaa analyysin"""
    try:
        # Haetaan URL käyttäjän lomakkeesta
        url = request.form.get('url')
        
        if not url:
            return jsonify({'error': 'URL-osoite puuttuu'}), 400
        
        # Tarkistetaan, että URL on Oikotien asunto-URL
        if 'oikotie.fi' not in url and 'asunnot.oikotie.fi' not in url:
            return jsonify({'error': 'Syötä kelvollinen Oikotie-asuntolinkin URL'}), 400
        
        # Käytetään scraperia hakemaan asuntotiedot
        logger.info(f"Haetaan tietoja URL:sta: {url}")
        scraper = RealEstateScraper(url)
        success = scraper.run()
        
        if not success:
            return jsonify({'error': 'Asunnon tietojen hakeminen epäonnistui'}), 500
        
        # Haetaan asunnon tiedot markdown-muodossa
        logger.info("Muunnetaan tiedot markdown-muotoon")
        markdown_data = scraper.format_to_markdown()
        
        if not markdown_data:
            logger.error("Markdown-datan luominen epäonnistui - tyhjä tulos")
            return jsonify({'error': 'Markdown-muotoisen datan luominen epäonnistui'}), 500
        
        logger.debug(f"Markdown-datan pituus: {len(markdown_data)} merkkiä")
        
        # Käytetään OpenAI API:a analyysin tekemiseen
        logger.info("Tehdään OpenAI API -kutsu analyysia varten")
        analysis_response = api_call.get_analysis(markdown_data)
        
        if not analysis_response:
            logger.error("API-kutsu palautti tyhjän vastauksen")
            return jsonify({'error': 'API-analyysi epäonnistui'}), 500
            
        # Varmistetaan että vastaus on puhdistettu (API:ssa puhdistus tehdään jo, tämä on varmuuden vuoksi)
        analysis_response = api_call.sanitize_markdown_response(analysis_response)
        
        # Sanitoidaan sisältö ennen template-renderöintiä
        sanitized_markdown = _sanitize_content(markdown_data)
        sanitized_analysis = _sanitize_content(analysis_response)
        
        logger.info("Renderöidään vastaussivu käyttäjälle")
        
        # Palautetaan sekä raakatiedot että analyysi
        return render_template('results.html', 
                            property_data=sanitized_markdown, 
                            analysis=sanitized_analysis)
        
    except Exception as e:
        logger.exception(f"Odottamaton virhe analyysin teossa: {e}")
        return jsonify({'error': f'Virhe: {str(e)}'}), 500

@app.route('/api/analyze', methods=['POST'])
def api_analyze():
    """API-pääte, joka ottaa vastaan URL:n ja palauttaa analyysin JSON-muodossa"""
    try:
        data = request.get_json()
        url = data.get('url')
        
        if not url:
            return jsonify({'error': 'URL-osoite puuttuu'}), 400
        
        # Tarkistetaan, että URL on Oikotien asunto-URL
        if 'oikotie.fi' not in url and 'asunnot.oikotie.fi' not in url:
            return jsonify({'error': 'Syötä kelvollinen Oikotie-asuntolinkin URL'}), 400
        
        # Käytetään scraperia hakemaan asuntotiedot
        scraper = RealEstateScraper(url)
        success = scraper.run()
        
        if not success:
            return jsonify({'error': 'Asunnon tietojen hakeminen epäonnistui'}), 500
        
        # Haetaan asunnon tiedot markdown-muodossa
        markdown_data = scraper.format_to_markdown()
        
        if not markdown_data:
            return jsonify({'error': 'Markdown-muotoisen datan luominen epäonnistui'}), 500
        
        # Käytetään OpenAI API:a analyysin tekemiseen
        analysis_response = api_call.get_analysis(markdown_data)
        
        # Varmistetaan että vastaus on puhdistettu (API:ssa puhdistus tehdään jo)
        analysis_response = api_call.sanitize_markdown_response(analysis_response)
        
        # Palautetaan sekä raakatiedot että analyysi JSON-muodossa
        return jsonify({
            'property_data': markdown_data,
            'analysis': analysis_response
        })
        
    except Exception as e:
        logger.error(f"Virhe API-analyysin teossa: {e}")
        return jsonify({'error': f'Virhe: {str(e)}'}), 500

@app.route('/analyses')
def list_analyses():
    """Näyttää kaikki tallennetut analyysit listana"""
    try:
        # Haetaan tallennetut analyysit
        analyses_files = api_call.get_saved_analyses()
        
        analyses_list = []
        for filepath in analyses_files:
            filename = os.path.basename(filepath)
            # Parsitaan tiedostosta päivämäärä ja tunnus
            parts = filename.replace('.txt', '').split('_')
            if len(parts) >= 3:
                date_str = parts[1]
                time_str = parts[2] if len(parts) > 3 else ""
                
                # Formatoidaan päivämäärä luettavampaan muotoon
                if len(date_str) == 8:  # YYYYMMDD
                    formatted_date = f"{date_str[6:8]}.{date_str[4:6]}.{date_str[:4]}"
                else:
                    formatted_date = date_str
                
                # Yritetään lukea otsikko tiedoston ensimmäisiltä riveiltä
                title = ""
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for i, line in enumerate(f):
                            if i > 5:  # Luetaan vain ensimmäiset rivit
                                break
                            if line.startswith("Kohde:"):
                                title = line.replace("Kohde:", "").strip()
                                break
                except Exception as e:
                    logger.warning(f"Virhe tiedoston lukemisessa: {e}")
                
                if not title:
                    title = f"Analyysi {formatted_date}"
                
                analyses_list.append({
                    'filename': filename,
                    'title': title,
                    'date': formatted_date,
                    'time': time_str
                })
        
        return render_template('analyses.html', analyses=analyses_list)
        
    except Exception as e:
        logger.exception(f"Virhe analyysien listaamisessa: {e}")
        return jsonify({'error': f'Virhe analyysien listaamisessa: {str(e)}'}), 500

@app.route('/analysis/<filename>')
def view_analysis(filename):
    """Näyttää yksittäisen tallennetun analyysin"""
    try:
        # Tarkista että tiedostonimi on turvallinen
        if not filename or '..' in filename or '/' in filename:
            return jsonify({'error': 'Virheellinen tiedostonimi'}), 400
            
        # Muodosta tiedostopolku
        filepath = os.path.join(api_call.ANALYSES_DIR, filename)
        
        # Tarkista että tiedosto on olemassa
        if not os.path.exists(filepath):
            return jsonify({'error': 'Analyysiä ei löytynyt'}), 404
            
        # Lue tiedoston sisältö
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Hae otsikko tiedostosta
        title = "Asuntoanalyysi"
        for line in content.split('\n')[:10]:
            if line.startswith("Kohde:"):
                title = line.replace("Kohde:", "").strip()
                break
                
        # Sanitoi sisältö
        content = _sanitize_content(content)
            
        return render_template('analysis.html', title=title, content=content, filename=filename)
        
    except Exception as e:
        logger.exception(f"Virhe analyysin näyttämisessä: {e}")
        return jsonify({'error': f'Virhe analyysin näyttämisessä: {str(e)}'}), 500

@app.route('/analysis/raw/<filename>')
def download_analysis(filename):
    """Lataa analyysin raakasisällön tekstitiedostona"""
    try:
        # Tarkista että tiedostonimi on turvallinen
        if not filename or '..' in filename or '/' in filename:
            return jsonify({'error': 'Virheellinen tiedostonimi'}), 400
            
        return send_from_directory(
            os.path.abspath(api_call.ANALYSES_DIR),
            filename,
            as_attachment=True,
            mimetype='text/plain'
        )
        
    except Exception as e:
        logger.exception(f"Virhe analyysin lataamisessa: {e}")
        return jsonify({'error': f'Virhe analyysin lataamisessa: {str(e)}'}), 500

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
    
    app.run(debug=True) 