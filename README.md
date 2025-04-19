# Asuntoanalyysi

Sovellus, joka käyttää OpenAI API:a suomalaisten asuntoilmoitusten analysointiin. Sovellus antaa asiantuntevan analyysin asunnosta, sen hinnasta, sijainnista, ominaisuuksista ja mahdollisista riskeistä.

## Ominaisuudet

- Asuntotietojen automaattinen hakeminen Oikotie-palvelusta
- Tekoälyanalyysi asunnon tiedoista käyttäen OpenAI API:a
- Markdownin käyttö asuntotietojen ja analyysin esittämiseen
- Analyysien tallentaminen tekstitiedostoihin myöhempää tarkastelua varten
- Käyttäjäystävällinen verkkoliittymä

## Asennus

1. Kloonaa repositorio
2. Asenna riippuvuudet: `pip install -r requirements.txt`
3. Aseta OpenAI API-avain ympäristömuuttujaan: `export OPENAI_API_KEY=your-api-key-here`
4. Käynnistä sovellus: `python app.py`

## Käyttö

1. Avaa sovellus selaimessa: http://localhost:5000
2. Syötä Oikotie-asuntoilmoituksen URL
3. Klikkaa "Analysoi asunto"
4. Tarkastele analyysiä ja asunnon tietoja

## Tallennetut analyysit

Sovellus tallentaa automaattisesti kaikki tehdyt analyysit tekstitiedostoihin `analyses`-hakemistoon. Tallennetut analyysit ovat saatavilla myös sovelluksen käyttöliittymässä:

1. Klikkaa "Näytä tallennetut analyysit" etusivulla
2. Selaa tallennettuja analyysejä
3. Katso yksityiskohtia klikkaamalla analyysiä
4. Lataa analyysi tekstitiedostona tarvittaessa

## Teknologiat

- Python
- Flask
- OpenAI API
- BeautifulSoup
- Markdown

## Tekijänoikeudet

© 2024 Asuntoanalyysi - Kaikki oikeudet pidätetään 