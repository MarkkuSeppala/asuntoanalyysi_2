from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DecimalField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User

class LoginForm(FlaskForm):
    """Kirjautumislomake"""
    email = StringField('Sähköposti', validators=[DataRequired(), Email()])
    password = PasswordField('Salasana', validators=[DataRequired()])
    remember = BooleanField('Muista minut')
    submit = SubmitField('Kirjaudu')

class RegistrationForm(FlaskForm):
    """Rekisteröitymislomake"""
    email = StringField('Sähköposti', validators=[DataRequired(), Email()])
    password = PasswordField('Salasana', validators=[DataRequired(), Length(min=8, max=80)])
    confirm_password = PasswordField('Vahvista salasana', validators=[DataRequired(), EqualTo('password')])
    first_name = StringField('Etunimi', validators=[DataRequired(), Length(min=2, max=80)])
    last_name = StringField('Sukunimi', validators=[DataRequired(), Length(min=2, max=80)])
    street_address = StringField('Katuosoite', validators=[DataRequired(), Length(min=2, max=120)])
    postal_code = StringField('Postinumero', validators=[DataRequired(), Length(min=2, max=10)])
    city = StringField('Kaupunki', validators=[DataRequired(), Length(min=2, max=80)])
    state = StringField('Maakunta')
    country = StringField('Maa', default='Suomi')
    submit = SubmitField('Rekisteröidy')

    def validate_email(self, email):
        """Varmistaa, että sähköposti on uniikki"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Tämä sähköpostiosoite on jo käytössä. Ole hyvä ja valitse toinen.')

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