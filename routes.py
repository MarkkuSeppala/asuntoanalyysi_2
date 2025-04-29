from flask import render_template, redirect, url_for, flash, request
from flask_login import current_user, login_user
from werkzeug.urls import url_parse
from flask_app import app, db
from flask_app.forms import LoginForm, RegistrationForm
from flask_app.models import User

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Kirjautumissivu"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Kirjautuminen epäonnistui. Tarkista sähköposti ja salasana', 'danger')
    return render_template('login.html', title='Kirjaudu', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Rekisteröintisivu"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            street_address=form.street_address.data,
            postal_code=form.postal_code.data,
            city=form.city.data,
            state=form.state.data,
            country=form.country.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Rekisteröityminen onnistui! Voit nyt kirjautua sisään.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Rekisteröidy', form=form) 