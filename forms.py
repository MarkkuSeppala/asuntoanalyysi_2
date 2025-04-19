from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    """Kirjautumislomake"""
    username = StringField('Käyttäjätunnus', validators=[DataRequired()])
    password = PasswordField('Salasana', validators=[DataRequired()])
    remember = BooleanField('Muista minut')
    submit = SubmitField('Kirjaudu')

class RegistrationForm(FlaskForm):
    """Rekisteröitymislomake"""
    username = StringField('Käyttäjätunnus', validators=[
        DataRequired(),
        Length(min=3, max=20, message='Käyttäjätunnuksen täytyy olla 3-20 merkkiä pitkä')
    ])
    email = StringField('Sähköposti', validators=[
        DataRequired(),
        Email(message='Virheellinen sähköpostiosoite')
    ])
    password = PasswordField('Salasana', validators=[
        DataRequired(),
        Length(min=8, message='Salasanan täytyy olla vähintään 8 merkkiä pitkä')
    ])
    confirm_password = PasswordField('Vahvista salasana', validators=[
        DataRequired(),
        EqualTo('password', message='Salasanat eivät täsmää')
    ])
    submit = SubmitField('Rekisteröidy')
    
    def validate_username(self, username):
        """Tarkistaa, onko käyttäjätunnus jo käytössä"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Käyttäjätunnus on jo käytössä. Valitse toinen käyttäjätunnus.')
    
    def validate_email(self, email):
        """Tarkistaa, onko sähköpostiosoite jo käytössä"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Sähköpostiosoite on jo rekisteröity. Jos olet unohtanut salasanan, käytä salasanan palautustoimintoa.') 