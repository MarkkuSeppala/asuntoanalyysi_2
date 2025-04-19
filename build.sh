#!/usr/bin/env bash
# exit on error
set -o errexit

# Asennetaan riippuvuudet
pip install -r requirements.txt

# Varmistetaan että gunicorn on asennettu suoraan
pip install gunicorn

# Näytetään asennettu gunicorn-versio ja sijainti
echo "Gunicorn versio:"
pip show gunicorn

# Varmistetaan että start.sh on suoritettava
chmod +x start.sh

# Tarkistetaan että gunicorn on asennettu ja näkyy PATH:issa
python -m gunicorn --version || echo "VAROITUS: gunicorn ei toimi python -m kanssa"

# Varmistetaan että PATH sisältää asennetut paketit
export PATH=$PATH:$(python -m site --user-base)/bin:$HOME/.local/bin

# Tarkistetaan vielä kerran gunicorn
which gunicorn || echo "VAROITUS: gunicorn ei silti löydy järjestelmästä"

# Ei luoda tietokantaa vielä tässä vaiheessa, koska ympäristömuuttujia ei välttämättä ole saatavilla
# Tietokannan luonti tapahtuu sovelluksen käynnistyessä app.py:ssä olevan koodin kautta
echo "Build complete. Database will be initialized at startup."