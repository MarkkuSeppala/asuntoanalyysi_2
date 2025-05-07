#!/usr/bin/env python3

import os
import psycopg2
from urllib.parse import urlparse

# Yhdistä Render.com:in tietokantaan käyttäen ympäristömuuttujaa
db_url = os.environ.get('DATABASE_URL')

if not db_url:
    print("ERROR: DATABASE_URL-ympäristömuuttuja puuttuu!")
    exit(1)

# Parse database URL
url = urlparse(db_url)
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

# Yhdistä tietokantaan
try:
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Tarkista onko product_id-sarake jo olemassa
    cursor.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='subscriptions' AND column_name='product_id';
    """)
    
    if cursor.fetchone() is None:
        print("Lisätään product_id-sarake subscriptions-tauluun...")
        
        # Lisää product_id-sarake
        cursor.execute("""
            ALTER TABLE subscriptions 
            ADD COLUMN product_id VARCHAR(255);
        """)
        
        print("product_id-sarake lisätty onnistuneesti!")
    else:
        print("product_id-sarake on jo olemassa!")
    
    # Näytä taulun rakenne varmistukseksi
    cursor.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name='subscriptions';
    """)
    
    print("\nSubscriptions-taulun sarakkeet:")
    for row in cursor.fetchall():
        print(f"- {row[0]}: {row[1]}")
    
except Exception as e:
    print(f"Virhe: {e}")
finally:
    if 'conn' in locals():
        conn.close() 