"""Add subscription_type column

Revision ID: add_subscription_type
Revises: payment_system_01
Create Date: 2025-05-07 12:00:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_subscription_type'
down_revision = 'payment_system_01'
branch_labels = None
depends_on = None


def upgrade():
    # Add subscription_type column to subscriptions table
    op.add_column('subscriptions', sa.Column('subscription_type', sa.String(length=50), nullable=True))
    
    # Update existing rows to set subscription_type based on the associated product's type
    op.execute('''
        UPDATE subscriptions 
        SET subscription_type = (
            SELECT 
                CASE 
                    WHEN p.type = 'subscription' THEN 'monthly' 
                    WHEN p.type = 'one_time' THEN 'one_time'
                    ELSE 'monthly'
                END
            FROM products p 
            WHERE p.id = subscriptions.product_id
        )
    ''')
    
    # Make the column non-nullable after updating
    op.alter_column('subscriptions', 'subscription_type', nullable=False)


def downgrade():
    # Remove the column if needed
    op.drop_column('subscriptions', 'subscription_type') 