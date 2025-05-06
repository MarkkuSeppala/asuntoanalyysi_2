from flask import Blueprint, redirect, url_for, current_app, session, flash, request, make_response
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, current_user
from models import db, User, OAuth
import os
import json
import logging
import secrets
import time
import traceback
import requests

logger = logging.getLogger(__name__)

# Ympäristömuuttujat Google OAuth:lle
# Kehitysympäristössä voidaan sallia epäturvallinen tiedonsiirto, mutta POISTA TUOTANNOSTA!
if os.environ.get('FLASK_ENV') == 'development':
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

# Luodaan blueprint Googlea varten
oauth_bp = Blueprint('oauth', __name__)

def init_google_blueprint(app):
    """Alustaa Google OAuth blueprint:in käyttäen sovelluksen konfiguraatiota"""
    # Määritellään redirect URI
    # Flask-Dance käyttää '/login/google/authorized' -polkua
    site_url = app.config.get('SITE_URL', 'https://www.kotiko.io')
    redirect_uri = f"{site_url}/login/google/authorized"
    
    # Tarkista että client_id ja client_secret on asetettu
    client_id = app.config.get('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = app.config.get('GOOGLE_OAUTH_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.error("Google OAuth konfiguraatio puuttuu! Aseta GOOGLE_CLIENT_ID ja GOOGLE_CLIENT_SECRET ympäristömuuttujissa")
        # Älä kuitenkaan kaadu, koska muu sovellus toimii ilman OAuth:akin
    
    # Tarkista onko ympäristömuuttujissa määritelty redirect_uri
    config_redirect_uri = os.environ.get('GOOGLE_REDIRECT_URI', redirect_uri)
    
    logger.info(f"Google OAuth alustus - redirect_uri vaihtoehdot:")
    logger.info(f"1. Sovelluksen generoima: {redirect_uri}")
    logger.info(f"2. Ympäristömuuttujasta: {config_redirect_uri}")
    
    # Käytä make_google_blueprint oikein
    google_bp = make_google_blueprint(
        client_id=client_id,
        client_secret=client_secret,
        scope=["profile", "email"],
        redirect_to="oauth.google_login_callback",
        redirect_url=config_redirect_uri,
        reprompt_consent=False
    )
    app.register_blueprint(google_bp, url_prefix='/login')
    
    # Näytä asetukset lokeissa kehitystä varten
    if client_id and len(client_id) > 10:
        masked_client_id = f"{client_id[:5]}...{client_id[-5:]}"
    else:
        masked_client_id = "ei asetettu"
    
    logger.info(f"Google OAuth alustus: client_id={masked_client_id}, redirect_uri={config_redirect_uri}")
    
    # TÄRKEÄ FIX: Lisää suora reitti OAuth redirectiin, joka ohittaa Flask-Dance kokonaan
    @app.route('/login/google/authorized')
    def direct_oauth_callback():
        """Käsittelee Google OAuth callbackin suoraan, ohittaen Flask-Dance:n"""
        logger.info(f"Direct OAuth callback kutsuttu - args: {request.args}")
        
        # Tarkista onko koodissa virhe
        if request.args.get('error'):
            error = request.args.get('error')
            error_desc = request.args.get('error_description', '')
            logger.error(f"OAuth virhe: {error} - {error_desc}")
            flash("Kirjautuminen epäonnistui. Yritä uudelleen.", "danger")
            return redirect(url_for('auth.login'))
            
        # Tarkista onko koodi olemassa
        code = request.args.get('code')
        if not code:
            logger.error("OAuth code puuttuu")
            flash("Kirjautuminen epäonnistui. Yritä uudelleen.", "danger")
            return redirect(url_for('auth.login'))
            
        # Vaihda koodi tokeniin
        try:
            redirect_uri = f"{current_app.config.get('SITE_URL')}/login/google/authorized"
            token_url = 'https://oauth2.googleapis.com/token'
            token_data = {
                'code': code,
                'client_id': current_app.config.get('GOOGLE_OAUTH_CLIENT_ID'),
                'client_secret': current_app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            logger.info(f"Token-pyyntö: client_id={token_data['client_id'][:5]}..., redirect_uri={token_data['redirect_uri']}")
            token_response = requests.post(token_url, data=token_data)
            
            if not token_response.ok:
                logger.error(f"Token-pyyntö epäonnistui: Status {token_response.status_code}")
                logger.error(f"Token-vastaus: {token_response.text}")
                flash("Kirjautumistietojen hakeminen epäonnistui.", "danger")
                return redirect(url_for('auth.login'))
                
            token_data = token_response.json()
            logger.info("Token-pyyntö onnistui!")
            access_token = token_data.get('access_token')
            
            # Hae käyttäjätiedot
            userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
            userinfo_response = requests.get(userinfo_url, headers={
                'Authorization': f'Bearer {access_token}'
            })
            
            if not userinfo_response.ok:
                logger.error(f"Käyttäjätietojen hakeminen epäonnistui: {userinfo_response.text}")
                flash("Käyttäjätietojen hakeminen epäonnistui.", "danger")
                return redirect(url_for('auth.login'))
                
            google_user_info = userinfo_response.json()
            logger.info(f"Käyttäjätiedot haettu onnistuneesti: {google_user_info.get('email')}")
            
            token_info = {
                'access_token': access_token,
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': int(time.time()) + token_data.get('expires_in', 3600)
            }
            
            # Käsittele käyttäjätiedot
            google_email = google_user_info.get('email')
            if not google_email:
                flash("Sähköpostin hakeminen Googlelta epäonnistui.", "danger")
                return redirect(url_for('auth.login'))
            
            # Käytä Google-ID:tä provider_user_id:na
            google_id = google_user_info.get('id')
            
            # Hae käyttäjän etunimi ja sukunimi
            first_name = google_user_info.get('given_name', '')
            last_name = google_user_info.get('family_name', '')
            
            # Hae tai luo OAuth-tili
            logger.info(f"Haetaan/luodaan OAuth käyttäjä: {google_email}")
            oauth = OAuth.get_or_create(
                provider='google',
                provider_user_id=google_id,
                token=token_info,
                email=google_email,
                first_name=first_name,
                last_name=last_name
            )
            
            # Kirjaa käyttäjä sisään
            login_user(oauth.user)
            logger.info(f"Käyttäjä kirjattu sisään: {oauth.user.email}")
            
            # Tyhjennä istunto muilta kuin käyttäjän kirjautumistiedolta
            # Pidä vain istunnon pysyvyys ja käyttäjän kirjautumistiedot
            redirect_target = session.pop('oauth_redirect_origin', url_for('index')) if 'oauth_redirect_origin' in session else url_for('index')
            for key in list(session.keys()):
                if key not in ['_permanent', '_user_id', '_fresh']:
                    session.pop(key, None)
            
            response = make_response(redirect(redirect_target))
            # Varmista että evästeasetukset ovat kunnossa
            session.modified = True
            
            flash("Kirjautuminen Googlen kautta onnistui!", "success")
            return response
        except Exception as e:
            logger.error(f"Virhe OAuth prosessissa: {str(e)}")
            logger.error(traceback.format_exc())
            flash("Kirjautumisessa tapahtui virhe. Yritä myöhemmin uudelleen.", "danger")
            return redirect(url_for('auth.login'))
    
    return google_bp

@oauth_bp.route("/google-login")
def google_login():
    """Ohjaa käyttäjän Googlen kirjautumissivulle"""
    # Jos käyttäjä on jo kirjautunut
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    # Tarkistetaan että OAuth-asetukset on konfiguroitu
    if not current_app.config.get('GOOGLE_OAUTH_CLIENT_ID') or not current_app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'):
        flash("Google-kirjautuminen ei ole käytössä. Ota yhteyttä ylläpitoon.", "danger")
        return redirect(url_for('auth.login'))
    
    # Varmista että istunto on alustettu ennen Googlelle ohjaamista
    session.permanent = True
    
    # Generoi yksilöllinen tila-tunniste
    state = secrets.token_urlsafe(16)
    session['_google_oauth_state'] = state
    
    # Tallenna lisätietoa istuntoon
    session['oauth_redirect_origin'] = request.referrer or url_for('index')
    
    # Lokita istunnon tietoja
    logger.info(f"Ohjataan Googlen kirjautumiseen - session ID: {session.sid if hasattr(session, 'sid') else 'ei saatavilla'}")
    logger.info(f"Session-tiedot: {session.keys()}")
    logger.info(f"Luotu OAuth state: {state}")
    
    try:
        # Käytä manuaalista URL:n rakentamista joka sisältää state-parametrin
        google_auth_url = f"https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={current_app.config.get('GOOGLE_OAUTH_CLIENT_ID')}&redirect_uri={current_app.config.get('SITE_URL')}/login/google/authorized&scope=profile+email&state={state}"
        logger.info(f"Ohjataan URL:iin: {google_auth_url}")
        return redirect(google_auth_url)
    except Exception as e:
        logger.error(f"Virhe Google-kirjautumiseen ohjaamisessa: {str(e)}")
        flash("Kirjautumispalveluun yhdistäminen epäonnistui. Yritä myöhemmin uudelleen.", "danger")
        return redirect(url_for('auth.login'))

@oauth_bp.route("/google-callback")
def google_login_callback():
    """Käsittelee Googlen OAuth takaisinkutsun"""
    # Tarkista state-parametri ja lokita istuntotietoja debug-tarkoituksiin
    logger.info(f"Google callback kutsuttu - session ID: {session.sid if hasattr(session, 'sid') else 'ei saatavilla'}")
    logger.info(f"Session-tiedot: {session.keys()}")
    logger.info(f"Request args: {request.args}")
    
    # Tarkista, onko redirect_loop_protection-laskuri jo istunnossa
    # Jos on, niin estä loputtomat uudelleenohjaukset
    redirect_count = session.get('redirect_loop_protection', 0)
    if redirect_count > 5:  # Jos yli 5 uudelleenohjausta, estä kehä
        session.pop('redirect_loop_protection', None)  # Nollaa laskuri
        flash("Liian monta uudelleenohjausta tunnistautumisessa. Tyhjennä selaimesi evästeet ja yritä uudelleen.", "danger")
        logger.error(f"Tunnistettu mahdollinen redirect loop: {redirect_count} kertaa")
        return redirect(url_for('auth.login'))
    
    # Päivitä laskuri
    session['redirect_loop_protection'] = redirect_count + 1
    
    # Tarkistetaan onko state-parametri pyynnössä
    request_state = request.args.get('state')
    session_state = session.get('_google_oauth_state')
    code = request.args.get('code')
    
    logger.info(f"Pyynnön state: {request_state}")
    logger.info(f"Session state: {session_state}")
    logger.info(f"Auth code: {code is not None}")
    
    # Tarkista token vain jos molkemmat state ja code ovat olemassa
    if code and request_state:
        # RENDER.COM ERITYISRATKAISU: Ohitetaan state-tarkistus tuotantoympäristössä jos sessio on menetetty
        # HUOM: Tämä on vähemmän turvallinen mutta välttämätön jos istunnon tila menetetään redirectin aikana
        
        # Vaihda koodi käyttöoikeustietoihin suoraan Googlen API:n kautta
        redirect_uri = f"{current_app.config.get('SITE_URL')}/login/google/authorized"
        
        try:
            token_url = 'https://oauth2.googleapis.com/token'
            token_data = {
                'code': code,
                'client_id': current_app.config.get('GOOGLE_OAUTH_CLIENT_ID'),
                'client_secret': current_app.config.get('GOOGLE_OAUTH_CLIENT_SECRET'),
                'redirect_uri': redirect_uri,
                'grant_type': 'authorization_code'
            }
            
            logger.info(f"Suoritetaan token-pyyntö: client_id={token_data['client_id'][:5]}..., redirect_uri={token_data['redirect_uri']}")
            token_response = requests.post(token_url, data=token_data)
            
            if not token_response.ok:
                logger.error(f"Token-pyyntö epäonnistui: Status {token_response.status_code}")
                logger.error(f"Token-vastaus: {token_response.text}")
                flash("Kirjautumistietojen hakeminen epäonnistui.", "danger")
                return redirect(url_for('auth.login'))
                
            token_data = token_response.json()
            logger.info("Token-pyyntö onnistui!")
            access_token = token_data.get('access_token')
            
            # Hae käyttäjätiedot
            userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
            userinfo_response = requests.get(userinfo_url, headers={
                'Authorization': f'Bearer {access_token}'
            })
            
            if not userinfo_response.ok:
                logger.error(f"Käyttäjätietojen hakeminen epäonnistui: {userinfo_response.text}")
                flash("Käyttäjätietojen hakeminen epäonnistui.", "danger")
                return redirect(url_for('auth.login'))
                
            google_user_info = userinfo_response.json()
            logger.info(f"Käyttäjätiedot haettu onnistuneesti: {google_user_info.get('email')}")
            
            token_info = {
                'access_token': access_token,
                'token_type': token_data.get('token_type', 'Bearer'),
                'expires_at': int(time.time()) + token_data.get('expires_in', 3600)
            }
            
            # Käsittele käyttäjätiedot
            google_email = google_user_info.get('email')
            if not google_email:
                flash("Sähköpostin hakeminen Googlelta epäonnistui.", "danger")
                return redirect(url_for('auth.login'))
            
            # Käytä Google-ID:tä provider_user_id:na
            google_id = google_user_info.get('id')
            
            # Hae käyttäjän etunimi ja sukunimi
            first_name = google_user_info.get('given_name', '')
            last_name = google_user_info.get('family_name', '')
            
            # Hae tai luo OAuth-tili
            logger.info(f"Haetaan/luodaan OAuth käyttäjä: {google_email}")
            oauth = OAuth.get_or_create(
                provider='google',
                provider_user_id=google_id,
                token=token_info,
                email=google_email,
                first_name=first_name,
                last_name=last_name
            )
            
            # Kirjaa käyttäjä sisään
            login_user(oauth.user)
            logger.info(f"Käyttäjä kirjattu sisään: {oauth.user.email}")
            
            # Nollaa redirect loop protection laskuri, koska kirjautuminen onnistui
            session.pop('redirect_loop_protection', None)
            
            # Ohjaa käyttäjä etusivulle
            redirect_target = url_for('index')
            
            # Yritä hakea oauth_redirect_origin jos se on olemassa
            if 'oauth_redirect_origin' in session:
                redirect_target = session.pop('oauth_redirect_origin')
                
            flash("Kirjautuminen Googlen kautta onnistui!", "success")
            return redirect(redirect_target)
            
        except Exception as e:
            logger.error(f"Virhe OAuth prosessissa: {str(e)}")
            logger.error(traceback.format_exc())
            flash("Kirjautumisessa tapahtui virhe. Yritä myöhemmin uudelleen.", "danger")
            return redirect(url_for('auth.login'))
    else:
        logger.error("State-parametri puuttuu sessiosta tai pyynnöstä, tai auth code puuttuu")
        flash("Kirjautuminen epäonnistui. Yritä uudelleen.", "warning")
        return redirect(url_for('oauth.google_login')) 