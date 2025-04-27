#!/bin/bash
# Aktivoidaan virtuaaliympäristö
source .venv/bin/activate
# Käynnistetään gunicorn virtuaaliympäristön sisällä useammalla työprosessilla
gunicorn wsgi:app --workers=4 --threads=2 --timeout=120