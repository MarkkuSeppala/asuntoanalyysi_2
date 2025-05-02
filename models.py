from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Käyttäjän malli, sisältää authentication ja profile tiedot
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    api_calls_count = db.Column(db.Integer, default=0)
    
    # Henkilötiedot
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    street_address = db.Column(db.String(100))
    postal_code = db.Column(db.String(10))
    city = db.Column(db.String(50))
    state = db.Column(db.String(50))
    country = db.Column(db.String(50))
    
    # Analyysit, jotka käyttäjä on tehnyt
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    
    @property
    def password(self):
        """Estää salasanan lukemisen."""
        raise AttributeError('password ei ole luettava attribuutti')
    
    @password.setter
    def password(self, password):
        """Asettaa salasanan hash-arvon."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Tarkistaa salasanan oikeellisuuden."""
        return check_password_hash(self.password_hash, password)
    
    def increment_api_calls(self):
        """Kasvattaa API-kutsujen laskuria."""
        self.api_calls_count += 1
        db.session.commit()
    
    def has_reached_api_limit(self, limit=100):
        """Tarkistaa onko käyttäjä saavuttanut API-kutsujen rajan."""
        return self.api_calls_count >= limit
    
    def can_make_api_call(self):
        """Tarkistaa voiko käyttäjä tehdä API-kutsun.
        Admin-käyttäjillä tai käyttäjillä, jotka eivät ole saavuttaneet rajaa, on oikeus."""
        return self.is_admin or not self.has_reached_api_limit(2)  # Rajoitus 2 kutsuun tavallisille käyttäjille
    
    def __repr__(self):
        """Palauttaa käyttäjän esitysmuodon."""
        return f'<User {self.email}>'

class Analysis(db.Model):
    """Analyysimalli tietokantaa varten"""
    __tablename__ = 'analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255), nullable=True)
    property_url = db.Column(db.String(500), nullable=True)
    content = db.Column(db.Text, nullable=True)  # Analyysisisältö tekstimuodossa
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Kohteet, jotka on liitetty tähän analyysiin
    kohde = db.relationship('Kohde', backref='analysis', lazy=True, uselist=False)
    
    def __repr__(self):
        return f'<Analysis {self.title}>'

class RiskAnalysis(db.Model):
    """Riskianalyysimalli tietokantaa varten"""
    __tablename__ = 'risk_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    risk_data = db.Column(db.Text, nullable=False)  # JSON-muotoinen riskianalyysi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Määritellään suhde Analysis-tauluun
    analysis = db.relationship('Analysis', backref=db.backref('risk_analysis', lazy=True, uselist=False))
    
    # Määritellään suhde User-tauluun
    user = db.relationship('User', backref=db.backref('risk_analyses', lazy=True))
    
    def __repr__(self):
        return f'<RiskAnalysis for Analysis {self.analysis_id}>'

class Kohde(db.Model):
    """Kohteiden tietomalli tietokantaa varten"""
    __tablename__ = 'kohteet'
    
    id = db.Column(db.Integer, primary_key=True)
    osoite = db.Column(db.String(255), nullable=False)
    tyyppi = db.Column(db.String(50), nullable=True)  # omakotitalo, kerrostalo, rivitalo, erillistalo, paritalo
    hinta = db.Column(db.Numeric, nullable=True)
    rakennusvuosi = db.Column(db.Integer, nullable=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    risk_level = db.Column(db.Numeric(3, 1), nullable=True)  # Riskitaso asteikolla 1-10, 1 desimaalin tarkkuudella
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # Käyttäjä, jolle kohde kuuluu
    
    # Käyttäjäsuhde
    user = db.relationship('User', backref=db.backref('kohteet', lazy=True))
    
    def __repr__(self):
        return f'<Kohde {self.osoite}>' 