from flask import Blueprint, redirect, url_for, current_app, session, flash, request
from flask_dance.contrib.google import make_google_blueprint, google
from flask_login import login_user, current_user
from models import db, User, OAuth
import os
import json
import logging

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
        reprompt_consent=False,
        # Päivitetään istuntoasetukset
        storage_kwargs={
            "secure": app.config.get("SESSION_COOKIE_SECURE", True),
            "httponly": app.config.get("SESSION_COOKIE_HTTPONLY", True),
            "samesite": app.config.get("SESSION_COOKIE_SAMESITE", "Lax")
        }
    )
    app.register_blueprint(google_bp, url_prefix='/login')
    
    # Näytä asetukset lokeissa kehitystä varten
    if client_id and len(client_id) > 10:
        masked_client_id = f"{client_id[:5]}...{client_id[-5:]}"
    else:
        masked_client_id = "ei asetettu"
    
    logger.info(f"Google OAuth alustus: client_id={masked_client_id}, redirect_uri={config_redirect_uri}")
    
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
    # Tallenna lisätietoa istuntoon
    session['oauth_redirect_origin'] = request.referrer or url_for('index')
    
    # Lokita istunnon tietoja
    logger.info(f"Ohjataan Googlen kirjautumiseen - session ID: {session.sid if hasattr(session, 'sid') else 'ei saatavilla'}")
    logger.info(f"Session-tiedot: {session.keys()}")
    
    try:
        return redirect(url_for('google.login'))
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
    
    # Tarkista että Google-blueprintilla on pääsy tokeniin
    if not google.authorized:
        logger.error("Google ei ole autentikoitu - state saattaa puuttua")
        if 'state' in request.args:
            logger.info(f"Pyynnön state parametri: {request.args.get('state')}")
            logger.info("Tarkistetaan vastaako state sessiota...")
            if hasattr(session, 'get') and session.get('_google_oauth_state'):
                logger.info(f"Session state: {session.get('_google_oauth_state')}")
                if session.get('_google_oauth_state') != request.args.get('state'):
                    logger.error("State parametri ei täsmää session statea!")
        
        flash("Kirjautuminen Googlen kautta epäonnistui. State-parametri puuttuu. Tyhjennä selaimesi evästeet ja yritä uudelleen.", "danger")
        return redirect(url_for('auth.login'))
    
    # Hae käyttäjän tiedot Googlelta
    try:
        resp = google.get("/oauth2/v1/userinfo")
        if not resp.ok:
            flash("Käyttäjätietojen hakeminen Googlelta epäonnistui.", "danger")
            logger.error(f"Google API virhe: {resp.text}")
            return redirect(url_for('auth.login'))
        
        google_user_info = resp.json()
        logger.info(f"Google käyttäjätiedot haettu onnistuneesti: {google_user_info.get('email')}")
        
        # Tarkista, että sähköposti on saatavilla
        google_email = google_user_info.get('email')
        if not google_email:
            flash("Sähköpostin hakeminen Googlelta epäonnistui.", "danger")
            return redirect(url_for('auth.login'))
        
        # Käytä Google-ID:tä provider_user_id:na
        google_id = google_user_info.get('id')
        
        # Hae käyttäjän etunimi ja sukunimi
        first_name = google_user_info.get('given_name', '')
        last_name = google_user_info.get('family_name', '')
        
        # Tallenna token-tiedot
        token_info = {
            'access_token': google.token['access_token'],
            'token_type': google.token.get('token_type', 'Bearer'),
            'expires_at': google.token.get('expires_at', None)
        }
        
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
        
        # Ohjaa käyttäjä etusivulle tai alkuperäiseen kohteeseen
        redirect_target = session.pop('oauth_redirect_origin', url_for('index'))
        flash("Kirjautuminen Googlen kautta onnistui!", "success")
        return redirect(redirect_target)
        
    except Exception as e:
        logger.error(f"Virhe Google OAuth -prosessissa: {str(e)}")
        flash("Kirjautumisessa tapahtui virhe. Yritä myöhemmin uudelleen.", "danger")
        return redirect(url_for('auth.login')) 