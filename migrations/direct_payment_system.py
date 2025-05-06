"""
Script to directly create payment system tables using SQLAlchemy
"""
import os
import sys
from datetime import datetime
from flask import Flask
import sqlalchemy as sa
from sqlalchemy.orm import scoped_session, sessionmaker

# Add the parent directory to the Python path so we can import modules from there
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import the models and db instance
from models import db, User, Product, Payment, Subscription

def create_app():
    """Create and configure the Flask app"""
    app = Flask(__name__)
    
    # Configure database
    database_url = os.environ.get('DATABASE_URL', 'sqlite:///../flask_database.db')
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize the db with the app
    db.init_app(app)
    
    return app

def create_payment_system():
    """
    Create the payment system tables and add initial data
    """
    app = create_app()
    
    with app.app_context():
        print("Creating payment system tables...")
        
        inspector = sa.inspect(db.engine)
        tables = inspector.get_table_names()
        
        # Create the 'products' table if it doesn't exist
        if 'products' not in tables:
            print("Creating 'products' table...")
            class ProductBase(db.Model):
                __tablename__ = 'products'
                id = sa.Column(sa.Integer, primary_key=True)
                name = sa.Column(sa.String(128), nullable=False)
                price = sa.Column(sa.Float, nullable=False)
                description = sa.Column(sa.Text, nullable=True)
                type = sa.Column(sa.String(32), nullable=False)  # 'subscription' or 'one_time'
                analyses_count = sa.Column(sa.Integer, nullable=True)  # For 'one_time' products
                duration_days = sa.Column(sa.Integer, nullable=True)  # For 'subscription' products
                created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
                active = sa.Column(sa.Boolean, nullable=False, default=True)
                
            # Create the table
            db.create_all()
            
            # Add default products
            print("Adding default products...")
            products = [
                Product(
                    name='Kuukausitilaus',
                    price=9.90,
                    description='Kuukausitilaus, jolla saat rajoittamattoman määrän analyysejä',
                    type='subscription',
                    duration_days=30,
                    active=True
                ),
                Product(
                    name='5 analyysiä',
                    price=3.90,
                    description='5 analyysiä, käytettävissä milloin vain',
                    type='one_time',
                    analyses_count=5,
                    active=True
                )
            ]
            
            db.session.add_all(products)
            db.session.commit()
            print("Default products added.")
        else:
            print("'products' table already exists.")
            
        # Create the 'payments' table if it doesn't exist
        if 'payments' not in tables:
            print("Creating 'payments' table...")
            class PaymentBase(db.Model):
                __tablename__ = 'payments'
                id = sa.Column(sa.Integer, primary_key=True)
                user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
                product_id = sa.Column(sa.Integer, sa.ForeignKey('products.id'), nullable=False)
                amount = sa.Column(sa.Float, nullable=False)
                status = sa.Column(sa.String(32), nullable=False)
                payment_method = sa.Column(sa.String(64), nullable=True)
                transaction_id = sa.Column(sa.String(128), nullable=True)
                subscription_id = sa.Column(sa.Integer, nullable=True)
                created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
                
            # Create the table
            db.create_all()
            print("'payments' table created.")
        else:
            print("'payments' table already exists.")
            
        # Check if 'subscriptions' table exists, and if not, create it
        if 'subscriptions' not in tables:
            print("Creating 'subscriptions' table...")
            class SubscriptionBase(db.Model):
                __tablename__ = 'subscriptions'
                id = sa.Column(sa.Integer, primary_key=True)
                user_id = sa.Column(sa.Integer, sa.ForeignKey('users.id'), nullable=False)
                product_id = sa.Column(sa.Integer, sa.ForeignKey('products.id'), nullable=False)
                subscription_type = sa.Column(sa.String(32), nullable=False)
                status = sa.Column(sa.String(32), nullable=False)
                start_date = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
                expires_at = sa.Column(sa.DateTime, nullable=True)
                next_billing_date = sa.Column(sa.DateTime, nullable=True)
                last_payment_date = sa.Column(sa.DateTime, nullable=True)
                payment_id = sa.Column(sa.String(128), nullable=True)
                created_at = sa.Column(sa.DateTime, nullable=False, default=datetime.utcnow)
                
            # Create the table
            db.create_all()
            print("'subscriptions' table created.")
        else:
            print("'subscriptions' table already exists.")
            
        # Check if 'users' table has 'analyses_left' column, and if not, add it
        users_columns = [col['name'] for col in inspector.get_columns('users')]
        if 'analyses_left' not in users_columns:
            print("Adding 'analyses_left' column to 'users' table...")
            with db.engine.begin() as conn:
                conn.execute(sa.text("ALTER TABLE users ADD COLUMN analyses_left INTEGER NOT NULL DEFAULT 0"))
            print("'analyses_left' column added to 'users' table.")
        else:
            print("'analyses_left' column already exists in 'users' table.")
            
        print("Payment system setup complete!")

if __name__ == "__main__":
    create_payment_system() 