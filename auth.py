from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User
from forms import LoginForm, RegistrationForm

# Luodaan Blueprint autentikaatioreiteille
auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Kirjautumissivu"""
    # Tarkistetaan onko kyseessä API-kutsu vai tavallinen selainpyyntö
    if request.is_json:
        data = request.get_json()
        user = User.query.filter_by(email=data.get('email')).first()
        
        if user and user.check_password(data.get('password')):
            login_user(user)
            return jsonify({
                'status': 'success',
                'message': 'Kirjautuminen onnistui',
                'user': {
                    'id': user.id,
                    'email': user.email,
                    'name': user.username
                }
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Virheelliset kirjautumistiedot'
            }), 401

    # Jos käyttäjä on jo kirjautunut, ohjataan etusivulle
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Tarkistetaan käyttäjänimi ja salasana
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            
            # Ohjataan käyttäjä sinne mihin hän oli menossa, tai etusivulle
            return redirect(next_page or url_for('index'))
        else:
            flash('Kirjautuminen epäonnistui. Tarkista käyttäjätunnus ja salasana.', 'danger')
    
    return render_template('login.html', form=form)

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Rekisteröitymissivu"""
    # Tarkistetaan onko kyseessä API-kutsu vai tavallinen selainpyyntö
    if request.is_json:
        data = request.get_json()
        
        # Tarkistetaan onko sama sähköposti jo käytössä
        existing_user = User.query.filter_by(email=data.get('email')).first()
        if existing_user:
            return jsonify({
                'status': 'error',
                'message': 'Tämä sähköpostiosoite on jo käytössä'
            }), 400
        
        # Luodaan uusi käyttäjä
        user = User(
            username=data.get('name'),
            email=data.get('email'),
            password=data.get('password')
        )
        
        # Lisätään käyttäjä tietokantaan
        db.session.add(user)
        db.session.commit()
        
        # Kirjataan käyttäjä sisään heti rekisteröitymisen jälkeen
        login_user(user)
        
        return jsonify({
            'status': 'success',
            'message': 'Rekisteröityminen onnistui',
            'user': {
                'id': user.id,
                'email': user.email,
                'name': user.username
            }
        })

    # Jos käyttäjä on jo kirjautunut, ohjataan etusivulle
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Luodaan uusi käyttäjä
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        
        # Lisätään käyttäjä tietokantaan
        db.session.add(user)
        db.session.commit()
        
        # Kirjataan käyttäjä sisään heti rekisteröitymisen jälkeen
        login_user(user)
        
        flash('Rekisteröityminen onnistui! Tervetuloa käyttämään sovellusta.', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html', form=form)

@auth.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    """Kirjaa käyttäjän ulos"""
    logout_user()
    
    # Tarkistetaan onko kyseessä API-kutsu vai tavallinen selainpyyntö
    if request.is_json or request.method == 'POST':
        return jsonify({
            'status': 'success',
            'message': 'Olet kirjautunut ulos'
        })
    
    flash('Olet kirjautunut ulos.', 'info')
    return redirect(url_for('auth.login'))

@auth.route('/profile')
@login_required
def profile():
    """Käyttäjän profiilisivu"""
    return render_template('profile.html')

@auth.route('/api/user')
@login_required
def api_user():
    """Palauttaa kirjautuneen käyttäjän tiedot API-kutsua varten"""
    return jsonify({
        'status': 'success',
        'user': {
            'id': current_user.id,
            'email': current_user.email,
            'name': current_user.username
        }
    }) 