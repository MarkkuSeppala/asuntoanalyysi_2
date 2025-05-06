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
    # Määritellään redirect URI sivuston URL:n perusteella
    redirect_uri = f"{app.config.get('SITE_URL', 'https://www.kotiko.io')}/login/google/authorized"
    
    # Tarkista että client_id ja client_secret on asetettu
    client_id = app.config.get('GOOGLE_OAUTH_CLIENT_ID')
    client_secret = app.config.get('GOOGLE_OAUTH_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        logger.error("Google OAuth konfiguraatio puuttuu! Aseta GOOGLE_CLIENT_ID ja GOOGLE_CLIENT_SECRET ympäristömuuttujissa")
        # Älä kuitenkaan kaadu, koska muu sovellus toimii ilman OAuth:akin
    
    google_bp = make_google_blueprint(
        client_id=client_id,
        client_secret=client_secret,
        scope=["profile", "email"],
        redirect_to="oauth.google_login_callback",
        redirect_url=redirect_uri
    )
    app.register_blueprint(google_bp, url_prefix='/login')
    
    # Näytä asetukset lokeissa kehitystä varten
    if client_id and len(client_id) > 10:
        masked_client_id = f"{client_id[:5]}...{client_id[-5:]}"
    else:
        masked_client_id = "ei asetettu"
    
    logger.info(f"Google OAuth alustus: client_id={masked_client_id}, redirect_uri={redirect_uri}")
    
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
        
    return redirect(url_for('google.login'))

@oauth_bp.route("/google-callback")
def google_login_callback():
    """Käsittelee Googlen OAuth takaisinkutsun"""
    # Tarkista että Google-blueprintilla on pääsy tokeniin
    if not google.authorized:
        flash("Kirjautuminen Googlen kautta epäonnistui.", "danger")
        return redirect(url_for('auth.login'))
    
    # Hae käyttäjän tiedot Googlelta
    try:
        resp = google.get("/oauth2/v1/userinfo")
        if not resp.ok:
            flash("Käyttäjätietojen hakeminen Googlelta epäonnistui.", "danger")
            logger.error(f"Google API virhe: {resp.text}")
            return redirect(url_for('auth.login'))
        
        google_user_info = resp.json()
        
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
        
        # Ohjaa käyttäjä etusivulle
        flash("Kirjautuminen Googlen kautta onnistui!", "success")
        return redirect(url_for('index'))
        
    except Exception as e:
        logger.error(f"Virhe Google OAuth -prosessissa: {str(e)}")
        flash("Kirjautumisessa tapahtui virhe. Yritä myöhemmin uudelleen.", "danger")
        return redirect(url_for('auth.login')) 