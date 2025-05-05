from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User
from forms import LoginForm, RegistrationForm
from verification import generate_verification_token, save_verification_token, validate_token, mark_email_verified
from email_service import send_verification_email
import logging

logger = logging.getLogger(__name__)

# Luodaan Blueprint autentikaatioreiteille
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Kirjautumissivu"""
    # Jos käyttäjä on jo kirjautunut, ohjataan etusivulle
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        # Tarkistetaan sähköposti ja salasana
        if user and user.check_password(form.password.data):
            # Tarkista että sähköposti on vahvistettu
            if not user.is_verified and not user.is_admin:
                flash('Sähköpostiosoitettasi ei ole vielä vahvistettu. Tarkista sähköpostisi tai pyydä uusi vahvistuslinkki.', 'warning')
                return redirect(url_for('auth.resend_verification'))
                
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            
            # Ohjataan käyttäjä sinne mihin hän oli menossa, tai etusivulle
            return redirect(next_page or url_for('index'))
        else:
            flash('Kirjautuminen epäonnistui. Tarkista sähköposti ja salasana.', 'danger')
    
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Rekisteröitymissivu"""
    # Jos käyttäjä on jo kirjautunut, ohjataan etusivulle
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Tarkistetaan että käyttöehdot on hyväksytty
        if not form.accept_tos.data:
            flash('Sinun täytyy hyväksyä käyttöehdot jatkaaksesi.', 'danger')
            return render_template('register.html', form=form)
        
        # Luodaan uusi käyttäjä kaikilla tiedoilla
        user = User(
            email=form.email.data,
            password=form.password.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            street_address=form.street_address.data,
            postal_code=form.postal_code.data,
            city=form.city.data,
            state="",  # Oletuksena tyhjä, Suomessa ei käytetä
            country="Suomi",  # Oletuksena Suomi
            is_verified=False  # Käyttäjä ei ole vielä vahvistanut sähköpostiaan
        )
        
        # Lisätään käyttäjä tietokantaan
        db.session.add(user)
        db.session.commit()
        
        # Luodaan vahvistustoken ja tallennetaan se käyttäjälle
        token = generate_verification_token()
        save_verification_token(user, token)
        
        # Lähetetään vahvistussähköposti
        send_verification_email(user.email, token, user.first_name)
        
        flash('Rekisteröityminen onnistui! Lähetimme sähköpostiisi vahvistuslinkin. Tarkista sähköpostisi ja vahvista tilisi jatkaaksesi.', 'success')
        return redirect(url_for('auth.verification_pending'))
    
    return render_template('register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    """Kirjaa käyttäjän ulos"""
    logout_user()
    flash('Olet kirjautunut ulos.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/profile')
@login_required
def profile():
    """Käyttäjän profiilisivu"""
    return render_template('profile.html')

@auth.route('/verify')
def verify():
    """Sähköpostin vahvistusreitti"""
    token = request.args.get('token')
    if not token:
        flash('Vahvistuslinkki on virheellinen.', 'danger')
        return redirect(url_for('auth.login'))
    
    user, status = validate_token(token)
    
    if status == 'invalid':
        flash('Vahvistuslinkki on virheellinen tai vanhentunut.', 'danger')
        return redirect(url_for('auth.login'))
    
    if status == 'expired':
        flash('Vahvistuslinkki on vanhentunut. Lähetämme sinulle uuden linkin.', 'warning')
        # Luodaan uusi token ja lähetetään uusi sähköposti
        new_token = generate_verification_token()
        save_verification_token(user, new_token)
        send_verification_email(user.email, new_token, user.first_name)
        return redirect(url_for('auth.verification_pending'))
    
    # Vahvistetaan käyttäjän sähköposti
    mark_email_verified(user)
    flash('Sähköpostiosoitteesi on nyt vahvistettu! Voit kirjautua sisään.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/verification-pending')
def verification_pending():
    """Sivu, joka näytetään käyttäjälle rekisteröitymisen jälkeen"""
    return render_template('verification_pending.html')

@auth.route('/resend-verification', methods=['GET', 'POST'])
def resend_verification():
    """Sivu ja toiminto vahvistussähköpostin uudelleenlähettämiseen"""
    if request.method == 'POST':
        email = request.form.get('email')
        if not email:
            flash('Sähköpostiosoite vaaditaan.', 'danger')
            return render_template('resend_verification.html')
        
        user = User.query.filter_by(email=email).first()
        if not user:
            # Älä paljasta käyttäjälle, että sähköposti ei ole järjestelmässä
            flash('Jos annettu sähköpostiosoite on rekisteröity järjestelmäämme, lähetämme uuden vahvistuslinkin.', 'info')
            return redirect(url_for('auth.login'))
        
        if user.is_verified:
            flash('Sähköpostiosoitteesi on jo vahvistettu. Voit kirjautua sisään.', 'info')
            return redirect(url_for('auth.login'))
        
        # Luodaan uusi token ja lähetetään uusi sähköposti
        token = generate_verification_token()
        save_verification_token(user, token)
        send_verification_email(user.email, token, user.first_name)
        
        flash('Uusi vahvistuslinkki on lähetetty sähköpostiisi.', 'success')
        return redirect(url_for('auth.verification_pending'))
    
    return render_template('resend_verification.html') 