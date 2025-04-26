# Asuntoanalyysi

Sovellus, joka käyttää OpenAI API:a suomalaisten asuntoilmoitusten analysointiin. Sovellus antaa asiantuntevan analyysin asunnosta, sen hinnasta, sijainnista, ominaisuuksista ja mahdollisista riskeistä.

## Ominaisuudet

- Asuntotietojen automaattinen hakeminen Oikotie- ja Etuovi-palveluista
- Tekoälyanalyysi asunnon tiedoista käyttäen OpenAI API:a
- Markdownin käyttö asuntotietojen ja analyysin esittämiseen
- Analyysien tallentaminen tietokantaan myöhempää tarkastelua varten
- Käyttäjäystävällinen verkkoliittymä (sekä perinteinen että React-pohjainen)
- Riskianalyysi asuntokohteelle

## Asennus

1. Kloonaa repositorio
2. Asenna riippuvuudet: `pip install -r requirements.txt`
3. Aseta OpenAI API-avain ympäristömuuttujaan: `export OPENAI_API_KEY=your-api-key-here`
4. Asenna Chrome-selain ja varmista, että ChromeDriver on saatavilla (vaaditaan Etuovi-tiedostojen lataamiseen)
5. Käynnistä sovellus: `python app.py`

## React-käyttöliittymä

Sovellus tukee myös React-pohjaista käyttöliittymää. React-sovellus täytyy rakentaa ennalta, ennen kuin se voidaan julkaista Render.com-alustalla.

### React-sovelluksen rakentaminen

1. Asenna Node.js (versio 14 tai uudempi)
2. Asenna React-sovelluksen riippuvuudet projektihakemistossa:
   ```
   npm install
   ```
3. Rakenna React-sovellus:
   ```
   npm run build
   ```
4. Varmista, että "build"-kansio on luotu projektin juureen

### React-sovelluksen käyttöönotto

React-sovelluksen build-kansio otetaan automaattisesti käyttöön, kun projekti julkaistaan Render.com-alustalla. Render-konfiguraatio löytyy `build.sh`-tiedostosta, joka kopioi React-buildin staattiset tiedostot oikeaan paikkaan julkaisun yhteydessä.

React-käyttöliittymä on saatavilla osoitteessa `/react` kun sovellus on julkaistu.

## Käyttö

1. Avaa sovellus selaimessa: http://localhost:5000 (perinteinen käyttöliittymä) tai http://localhost:5000/react (React-käyttöliittymä)
2. Syötä Oikotie- tai Etuovi-asuntoilmoituksen URL
3. Klikkaa "Analysoi asunto"
4. Tarkastele analyysiä ja asunnon tietoja

## Tallennetut analyysit

Sovellus tallentaa kaikki tehdyt analyysit tietokantaan. Tallennetut analyysit ovat saatavilla sovelluksen käyttöliittymässä:

1. Valitse "Analyysit" navigaatiovalikosta
2. Selaa tallennettuja analyysejä
3. Katso yksityiskohtia klikkaamalla analyysiä

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
- PostgreSQL
- React (frontend)
- OpenAI API
- BeautifulSoup
- Markdown
- Selenium (Etuovi-integraatio)
- PyPDF2 (PDF-käsittely)

## Tekijänoikeudet

© 2024 Asuntoanalyysi - Kaikki oikeudet pidätetään 