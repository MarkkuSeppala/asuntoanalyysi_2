from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """
    Käyttäjän malli, sisältää authentication ja profile tiedot
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    api_calls_count = db.Column(db.Integer, default=0)
    analyses_left = db.Column(db.Integer, default=0)  # Jäljellä olevien analyysien määrä
    
    # Email verification fields
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), nullable=True)
    verification_token_created_at = db.Column(db.DateTime, nullable=True)
    
    # Henkilötiedot
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    street_address = db.Column(db.String(120), nullable=False)
    postal_code = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    country = db.Column(db.String(80), nullable=False)
    
    # Analyysit, jotka käyttäjä on tehnyt
    analyses = db.relationship('Analysis', backref='user', lazy=True)
    
    # Tilaukset (subscriptions)
    subscriptions = db.relationship('Subscription', backref='user', lazy=True, cascade="all, delete")
    
    # Maksut
    payments = db.relationship('Payment', backref='user', lazy=True, cascade="all, delete")
    
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
        Admin-käyttäjillä, aktiivisella kuukausijäsenyydellä tai käyttäjillä, joilla on jäljellä olevia analyysejä, on oikeus."""
        # Admin-käyttäjillä on aina oikeus
        if self.is_admin:
            return True
            
        # Tarkistetaan onko käyttäjällä aktiivinen kuukausitilaus
        active_subscription = Subscription.query.filter_by(
            user_id=self.id, 
            status='active',
            subscription_type='monthly'
        ).first()
        
        if active_subscription:
            return True
            
        # Tarkistetaan onko käyttäjällä jäljellä olevia analyysejä
        return self.analyses_left > 0
    
    def decrement_analyses_left(self):
        """Vähentää käyttäjän jäljellä olevien analyysien määrää yhdellä."""
        if self.analyses_left > 0:
            self.analyses_left -= 1
            db.session.commit()
            return True
        return False
    
    def add_analyses(self, count=5):
        """Lisää käyttäjälle analyysejä."""
        self.analyses_left += count
        db.session.commit()
    
    def get_active_subscription(self):
        """Palauttaa käyttäjän aktiivisen tilauksen jos sellainen on."""
        return Subscription.query.filter_by(
            user_id=self.id,
            status='active'
        ).first()
    
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
    
    # Risk analysis relationship with cascade delete
    risk_analysis = db.relationship('RiskAnalysis', backref='analysis', lazy=True, uselist=False, 
                                    cascade="all, delete", passive_deletes=True)
    
    def __repr__(self):
        return f'<Analysis {self.title}>'

class RiskAnalysis(db.Model):
    """Riskianalyysimalli tietokantaa varten"""
    __tablename__ = 'risk_analyses'
    
    id = db.Column(db.Integer, primary_key=True)
    analysis_id = db.Column(db.Integer, db.ForeignKey('analyses.id', ondelete='CASCADE'), nullable=False)
    risk_data = db.Column(db.Text, nullable=False)  # JSON-muotoinen riskianalyysi
    created_at = db.Column(db.DateTime, server_default=db.func.now())  # Use server-side default now()
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_risk_analyses_user_id'), nullable=True)
    
    # Määritellään suhde User-tauluun
    user = db.relationship('User', backref=db.backref('risk_analyses', lazy=True))
    
    def __repr__(self):
        return f'<RiskAnalysis for Analysis {self.analysis_id}>'

class Product(db.Model):
    """Tuotemalli tietokantaa varten"""
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    product_type = db.Column(db.String(50), nullable=False)  # 'subscription' tai 'one_time'
    analyses_count = db.Column(db.Integer, nullable=True)  # Kertaostoksen analyysien määrä
    active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    
    # Tilaukset, jotka liittyvät tähän tuotteeseen
    subscriptions = db.relationship('Subscription', backref='product', lazy=True)
    
    # Maksut, jotka liittyvät tähän tuotteeseen
    payments = db.relationship('Payment', backref='product', lazy=True)
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Payment(db.Model):
    """Maksutietomalli tietokantaa varten"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('subscriptions.id', ondelete='SET NULL'), nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(50), nullable=True)
    transaction_id = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(50), nullable=False)  # 'pending', 'completed', 'failed', 'refunded'
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, nullable=True)
    
    # Tilaus, johon maksu liittyy
    subscription = db.relationship('Subscription', backref='payments', lazy=True)
    
    def __repr__(self):
        return f'<Payment {self.id} for User {self.user_id}, Status: {self.status}>'

class Subscription(db.Model):
    """Tilaustietomalli tietokantaa varten"""
    __tablename__ = 'subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    subscription_type = db.Column(db.String(50), nullable=False)  # 'monthly', 'one_time'
    status = db.Column(db.String(50), nullable=False, default='active')  # 'active', 'cancelled', 'expired'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=True)
    is_trial = db.Column(db.Boolean, nullable=False, default=False)
    next_billing_date = db.Column(db.DateTime, nullable=True)
    cancel_at_period_end = db.Column(db.Boolean, nullable=False, default=False)
    last_payment_date = db.Column(db.DateTime, nullable=True)
    payment_id = db.Column(db.String(100), nullable=True)  # Payment reference or transaction ID
    
    def is_active(self):
        """Tarkistaa onko tilaus aktiivinen."""
        if self.status != 'active':
            return False
            
        # Jos tilaus on määräaikainen, tarkistetaan onko se vanhentunut
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
            
        return True
    
    def cancel(self, immediate=False):
        """Peruuttaa tilauksen."""
        if immediate:
            self.status = 'cancelled'
            self.expires_at = datetime.utcnow()
        else:
            self.cancel_at_period_end = True
        db.session.commit()
    
    def renew(self, days=30):
        """Uusii tilauksen seuraavalle jaksolle."""
        self.next_billing_date = datetime.utcnow() + timedelta(days=days)
        self.expires_at = self.next_billing_date
        self.cancel_at_period_end = False
        db.session.commit()
    
    def __repr__(self):
        return f'<Subscription {self.subscription_type} for User {self.user_id}>'

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
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', name='fk_kohteet_users'), nullable=True)  # Käyttäjä, jolle kohde kuuluu
    neliot = db.Column(db.Float, nullable=True)  # Asuinpinta-ala neliömetreinä
    huoneet = db.Column(db.Integer, nullable=True)  # Huoneiden lukumäärä
    
    # Käyttäjäsuhde
    user = db.relationship('User', backref=db.backref('kohteet', lazy=True))
    
    def __repr__(self):
        return f'<Kohde {self.osoite}>' 