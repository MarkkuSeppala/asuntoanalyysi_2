#!/bin/bash
# Aktivoidaan virtuaaliympäristö
source .venv/bin/activate
# Käynnistetään gunicorn virtuaaliympäristön sisällä
gunicorn wsgi:app