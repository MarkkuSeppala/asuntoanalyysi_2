#!/usr/bin/env bash
# exit on error
set -o errexit

# Asennetaan Python-riippuvuudet
echo "Asennetaan Python-riippuvuudet..."
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

# DEBUG: Näytä projektin juurikansion tiedostot
echo "Projektin juurikansion sisältö:"
ls -la

# Jos React-build on jo tehty ennalta ja build-kansio on olemassa, kopioi se static-kansioon
if [ -d "build" ]; then
  echo "React build löydetty. Kopioidaan React-build static-kansioon..."
  
  # DEBUG: Näytä build-kansion sisältö
  echo "Build-kansion sisältö:"
  ls -la build/
  
  # Tarkista onko index.html olemassa
  if [ -f "build/index.html" ]; then
    echo "index.html löytyy build-kansiosta!"
  else
    echo "VAROITUS: index.html EI löydy build-kansiosta!"
  fi
  
  # Luo static/react-kansio ja kopioi tiedostot
  mkdir -p static/react
  cp -r build/* static/react/
  
  # Korjaa index.html tiedoston polut lisäämällä suhteelliset polut
  if [ -f "static/react/index.html" ]; then
    echo "Korjataan index.html tiedoston polut käyttämään suhteellisia polkuja..."
    # Korvataan etuliitteet suhteellisilla poluilla
    sed -i 's|href="/static/|href="static/|g' static/react/index.html
    sed -i 's|src="/static/|src="static/|g' static/react/index.html
    sed -i 's|href="/react/|href="|g' static/react/index.html
    sed -i 's|src="/react/|src="|g' static/react/index.html
    sed -i 's|href="/|href="|g' static/react/index.html
    sed -i 's|src="/|src="|g' static/react/index.html
    echo "index.html polut korjattu"
  fi
  
  # DEBUG: Näytä static/react-kansion sisältö kopioinnin jälkeen
  echo "static/react-kansion sisältö kopioinnin jälkeen:"
  ls -la static/react/
  
  # Tarkista onko index.html kopioitunut oikein
  if [ -f "static/react/index.html" ]; then
    echo "index.html kopioitu onnistuneesti static/react-kansioon!"
  else
    echo "VAROITUS: index.html EI ole kopioitunut static/react-kansioon!"
  fi
else
  echo "VAROITUS: build-kansiota ei löydy projektin juuresta!"
  echo "React-sovellus ei tule olemaan saatavilla."
fi

# Ei luoda tietokantaa vielä tässä vaiheessa, koska ympäristömuuttujia ei välttämättä ole saatavilla
# Tietokannan luonti tapahtuu sovelluksen käynnistyessä app.py:ssä olevan koodin kautta
echo "Build complete. Database will be initialized at startup."