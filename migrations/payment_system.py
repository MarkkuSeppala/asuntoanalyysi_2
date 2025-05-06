"""
Migraatioskripti maksujärjestelmälle
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# Revision identifier - tämä on se id mitä halutaan käyttää
# Kun yhdistät tähän valmiina olevaan kantaan
revision = 'payment_system_01'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Tuotteet-taulu
    op.create_table('products',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=128), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(length=32), nullable=False),  # 'subscription' or 'one_time'
        sa.Column('analyses_count', sa.Integer(), nullable=True),  # For 'one_time' products
        sa.Column('duration_days', sa.Integer(), nullable=True),  # For 'subscription' products
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Maksut-taulu
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('payment_method', sa.String(length=64), nullable=True),
        sa.Column('transaction_id', sa.String(length=128), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )
    
    # Tilaukset-taulu (jos se ei vielä ole olemassa)
    try:
        op.create_table('subscriptions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('start_date', sa.DateTime(), nullable=False, default=datetime.utcnow),
            sa.Column('end_date', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'])
        )
    except:
        # Jos tilaukset-taulu on jo olemassa, lisää siihen tarvittavat sarakkeet
        try:
            op.add_column('subscriptions', sa.Column('product_id', sa.Integer(), nullable=True))
            op.create_foreign_key(None, 'subscriptions', 'products', ['product_id'], ['id'])
        except:
            pass
    
    # Lisätään käyttäjätauluun analyses_left-sarake
    try:
        op.add_column('users', sa.Column('analyses_left', sa.Integer(), server_default='0', nullable=False))
    except:
        pass
    
    # Lisätään valmiit tuotteet
    op.bulk_insert(
        sa.table('products',
            sa.column('name', sa.String),
            sa.column('price', sa.Float),
            sa.column('description', sa.Text),
            sa.column('type', sa.String),
            sa.column('analyses_count', sa.Integer),
            sa.column('duration_days', sa.Integer)
        ),
        [
            # Kuukausitilaus
            {
                'name': 'Kuukausitilaus',
                'price': 9.90,
                'description': 'Kuukausitilaus, jolla saat rajoittamattoman määrän analyysejä',
                'type': 'subscription',
                'analyses_count': None,
                'duration_days': 30
            },
            # Kertaosto (5 analyysiä)
            {
                'name': '5 analyysiä',
                'price': 3.90,
                'description': '5 analyysiä, käytettävissä milloin vain',
                'type': 'one_time',
                'analyses_count': 5,
                'duration_days': None
            }
        ]
    )

def downgrade():
    # Poistetaan taulut käänteisessä järjestyksessä
    try:
        op.drop_column('users', 'analyses_left')
    except:
        pass
    
    try:
        op.drop_table('payments')
    except:
        pass
    
    try:
        op.drop_table('subscriptions')
    except:
        pass
    
    try:
        op.drop_table('products')
    except:
        pass 