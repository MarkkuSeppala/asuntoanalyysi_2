from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User
from forms import LoginForm, RegistrationForm

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
            country="Suomi"  # Oletuksena Suomi
        )
        
        # Lisätään käyttäjä tietokantaan
        db.session.add(user)
        db.session.commit()
        
        # Kirjataan käyttäjä sisään heti rekisteröitymisen jälkeen
        login_user(user)
        
        flash('Rekisteröityminen onnistui! Tervetuloa käyttämään sovellusta.', 'success')
        return redirect(url_for('index'))
    
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