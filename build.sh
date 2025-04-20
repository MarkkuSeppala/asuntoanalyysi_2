#!/bin/bash
set -e

echo "Asennetaan python-riippuvuudet..."
pip install -r requirements.txt

echo "Tarkistetaan npm:n saatavuus..."
if ! command -v npm &> /dev/null; then
    echo "npm ei ole asennettu, asennetaan Node.js..."
    apt-get update
    apt-get install -y nodejs npm
fi

echo "Varmistetaan että hakemistot ovat olemassa..."
mkdir -p static/dist

echo "Asennetaan React-sovelluksen riippuvuudet ja käännetään tuotantoversio..."
cd static/js/react-app
npm install
npm run build

echo "Build valmis!"