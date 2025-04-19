#!/usr/bin/env bash
# exit on error
set -o errexit

# Asennetaan riippuvuudet
pip install -r requirements.txt

# Ei luoda tietokantaa vielä tässä vaiheessa, koska ympäristömuuttujia ei välttämättä ole saatavilla
# Tietokannan luonti tapahtuu sovelluksen käynnistyessä app.py:ssä olevan koodin kautta
echo "Build complete. Database will be initialized at startup."