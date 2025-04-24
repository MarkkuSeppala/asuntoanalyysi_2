# Asuntoanalyysi

Sovellus, joka käyttää OpenAI API:a suomalaisten asuntoilmoitusten analysointiin. Sovellus antaa asiantuntevan analyysin asunnosta, sen hinnasta, sijainnista, ominaisuuksista ja mahdollisista riskeistä.

## Ominaisuudet

- Asuntotietojen automaattinen hakeminen Oikotie- ja Etuovi-palveluista
- Tekoälyanalyysi asunnon tiedoista käyttäen OpenAI API:a
- Markdownin käyttö asuntotietojen ja analyysin esittämiseen
- Analyysien tallentaminen tekstitiedostoihin myöhempää tarkastelua varten
- Käyttäjäystävällinen verkkoliittymä
- Riskianalyysi asuntokohteelle

## Asennus

1. Kloonaa repositorio
2. Asenna riippuvuudet: `pip install -r requirements.txt`
3. Aseta OpenAI API-avain ympäristömuuttujaan: `export OPENAI_API_KEY=your-api-key-here`
4. Asenna Chrome-selain ja varmista, että ChromeDriver on saatavilla (vaaditaan Etuovi-tiedostojen lataamiseen)
5. Käynnistä sovellus: `python app.py`

## Käyttö

1. Avaa sovellus selaimessa: http://localhost:5000
2. Syötä Oikotie- tai Etuovi-asuntoilmoituksen URL
3. Klikkaa "Analysoi asunto"
4. Tarkastele analyysiä ja asunnon tietoja

## Tallennetut analyysit

Sovellus tallentaa automaattisesti kaikki tehdyt analyysit tekstitiedostoihin `analyses`-hakemistoon. Tallennetut analyysit ovat saatavilla myös sovelluksen käyttöliittymässä:

1. Klikkaa "Näytä tallennetut analyysit" etusivulla
2. Selaa tallennettuja analyysejä
3. Katso yksityiskohtia klikkaamalla analyysiä
4. Lataa analyysi tekstitiedostona tarvittaessa

## Tuetut lähteet

### Oikotie
- Automaattinen sisällön haku ja jäsentely Oikotie-asuntoilmoituksista
- Tukee kaikkia Oikotie.fi-asuntoilmoituksia

### Etuovi
- PDF-tiedoston automaattinen lataus Etuovi.com-ilmoituksista
- PDF-sisällön muunnos tekstiksi ja analyysi
- Tukee kaikkia Etuovi.com-kohdesivuja

## Teknologiat

- Python
- Flask
- OpenAI API
- BeautifulSoup
- Markdown
- Selenium (Etuovi-integraatio)
- PyPDF2 (PDF-käsittely)

## Tekijänoikeudet

© 2024 Asuntoanalyysi - Kaikki oikeudet pidätetään 