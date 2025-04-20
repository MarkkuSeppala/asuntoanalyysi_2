from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model, UserMixin):
    """Käyttäjämalli tietokantaa varten"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    api_calls_count = db.Column(db.Integer, default=0)  # Laskuri API-kyselyille
    
    # Analyysit, jotka käyttäjä on tehnyt
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    
    def __init__(self, username, email, password, is_admin=False):
        self.username = username
        self.email = email
        self.password_hash = generate_password_hash(password)
        self.is_admin = is_admin
        self.api_calls_count = 0
    
    def check_password(self, password):
        """Tarkistaa salasanan oikeellisuuden"""
        return check_password_hash(self.password_hash, password)
    
    def can_make_api_call(self):
        """Tarkistaa voiko käyttäjä tehdä API-kutsun"""
        if self.is_admin:
            return True  # Admin-käyttäjät voivat tehdä rajattomasti kutsuja
        return self.api_calls_count < 2  # Tavalliset käyttäjät: max 2 kutsua
    
    def increment_api_call_count(self):
        """Kasvattaa API-kutsujen laskuria yhdellä"""
        self.api_calls_count += 1
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.username}>'

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
    
    def __repr__(self):
        return f'<Analysis {self.title}>' 