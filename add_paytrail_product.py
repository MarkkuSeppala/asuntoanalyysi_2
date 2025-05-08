import os
import sys
from datetime import datetime
from flask import Flask
from models import db, Product

# Create a minimal Flask app for database access
app = Flask(__name__)
app.config.from_object("config.DevConfig")  # Use development config
db.init_app(app)

def add_paytrail_product():
    """
    Add a test product for Paytrail payments
    """
    with app.app_context():
        # Check if test product exists
        product = Product.query.filter_by(id=1).first()
        
        if product:
            print(f"Product already exists: ID={product.id}, Name={product.name}, Price={product.price}€")
            return
            
        # Create the product if it doesn't exist
        new_product = Product(
            name="Analyysi 5-paketti",
            description="5 asuntoanalyysiä käytettävissä milloin haluat",
            price=3.90,
            product_type="one_time",
            analyses_count=5,
            active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.session.add(new_product)
        db.session.commit()
        
        print(f"Added new product: ID={new_product.id}, Name={new_product.name}, Price={new_product.price}€")

if __name__ == "__main__":
    add_paytrail_product() 