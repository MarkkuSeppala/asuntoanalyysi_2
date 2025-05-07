"""Update product prices and features

Revision ID: update_product_prices
Revises: payment_system_01
Create Date: 2023-11-25 10:00:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
revision = 'update_product_prices'
down_revision = 'payment_system_01'
branch_labels = None
depends_on = None


def upgrade():
    # Update the monthly subscription product to have unlimited analyses
    op.execute("""
    UPDATE products
    SET description = 'Kuukausitilaus, jolla saat rajoittamattoman määrän analyysejä'
    WHERE product_type = 'subscription' AND name = 'Kuukausitilaus'
    """)
    
    # Update the one-time package price and analyses count
    op.execute("""
    UPDATE products
    SET price = 3.90, 
        description = '5 analyysiä, käytettävissä milloin vain',
        analyses_count = 5
    WHERE product_type = 'one_time' AND name = '5 analyysiä'
    """)


def downgrade():
    # Revert changes if needed
    op.execute("""
    UPDATE products
    SET description = 'Kuukausitilaus, jolla saat jopa 300 analyysiä kuukaudessa'
    WHERE product_type = 'subscription' AND name = 'Kuukausitilaus'
    """)
    
    op.execute("""
    UPDATE products
    SET price = 2.90, 
        description = '20 analyysiä, käytettävissä milloin vain',
        analyses_count = 20
    WHERE product_type = 'one_time' AND name = '5 analyysiä'
    """) 