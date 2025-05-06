"""Payment system migration

Revision ID: payment_system_01
Revises: 
Create Date: 2025-05-06 14:10:00

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers, used by Alembic.
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
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
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
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'])
    )
    
    # Tilaukset-taulu (jos se ei vielä ole olemassa)
    tables = op.get_bind().engine.table_names()
    if 'subscriptions' not in tables:
        op.create_table('subscriptions',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('product_id', sa.Integer(), nullable=False),
            sa.Column('start_date', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('end_date', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=32), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id'),
            sa.ForeignKeyConstraint(['user_id'], ['users.id']),
            sa.ForeignKeyConstraint(['product_id'], ['products.id'])
        )
    else:
        # Jos tilaukset-taulu on jo olemassa, tarkistetaan onko product_id-sarake jo olemassa
        conn = op.get_bind()
        inspector = sa.inspect(conn)
        columns = [col['name'] for col in inspector.get_columns('subscriptions')]
        if 'product_id' not in columns:
            op.add_column('subscriptions', sa.Column('product_id', sa.Integer(), nullable=True))
            op.create_foreign_key(None, 'subscriptions', 'products', ['product_id'], ['id'])
    
    # Lisätään käyttäjätauluun analyses_left-sarake
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'analyses_left' not in columns:
        op.add_column('users', sa.Column('analyses_left', sa.Integer(), server_default='0', nullable=False))
    
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
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Poistetaan analyses_left-sarake users-taulusta
    columns = [col['name'] for col in inspector.get_columns('users')] if 'users' in inspector.get_table_names() else []
    if 'analyses_left' in columns:
        op.drop_column('users', 'analyses_left')
    
    # Poistetaan taulut
    if 'payments' in inspector.get_table_names():
        op.drop_table('payments')
    
    if 'subscriptions' in inspector.get_table_names():
        # Jos subscription-taulua ei poisteta, poistetaan vain foreign key ja product_id-sarake
        columns = [col['name'] for col in inspector.get_columns('subscriptions')]
        if 'product_id' in columns:
            fk_name = None
            for fk in inspector.get_foreign_keys('subscriptions'):
                if fk['referred_table'] == 'products':
                    fk_name = fk['name']
                    break
            if fk_name:
                op.drop_constraint(fk_name, 'subscriptions', type_='foreignkey')
            op.drop_column('subscriptions', 'product_id')
    
    if 'products' in inspector.get_table_names():
        op.drop_table('products') 