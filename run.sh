#!/usr/bin/env bash

# Varmistetaan että PATH sisältää asennetut paketit
export PATH=$PATH:$(python -m site --user-base)/bin

# Käynnistetään sovellus
echo "Käynnistetään sovellus gunicornilla..."
gunicorn app:app 