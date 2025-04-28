# Asuntoanalyysi

Sovellus, joka käyttää OpenAI API:a suomalaisten asuntoilmoitusten analysointiin. Sovellus antaa asiantuntevan analyysin asunnosta, sen hinnasta, sijainnista, ominaisuuksista ja mahdollisista riskeistä.

## Ominaisuudet

- Asuntotietojen automaattinen hakeminen Oikotie- ja Etuovi-palveluista
- Tekoälyanalyysi asunnon tiedoista käyttäen OpenAI API:a
- Markdownin käyttö asuntotietojen ja analyysin esittämiseen
- Analyysien tallentaminen tekstitiedostoihin myöhempää tarkastelua varten
- Käyttäjäystävällinen verkkoliittymä
- Riskianalyysi asuntokohteelle

## Kehitysympäristön asennus Dockerilla

### Vaatimukset
- Docker ja Docker Compose asennettuna
- Git

### Asennus ja käynnistys

1. Kloonaa repositorio
```
git clone <repository-url>
cd asuntoanalyysi
```

2. Kopioi ympäristömuuttujat
```
cp .env-example .env
```
Muokkaa `.env` tiedostoa tarvittaessa (lisää esim. OpenAI API-avain).

3. Käynnistä Docker-kontit
```
docker-compose up -d
```

4. Sovellus on nyt käytettävissä osoitteessa http://localhost:5000

### Kehitys Dockerin kanssa

Kun muokkaat tiedostoja paikallisesti, Flask-sovellus lataa muutokset automaattisesti kehitystilassa. Docker-kontti jakaa sovelluksen tiedostot volumes-määritysten avulla.

### Konsoliyhteys konttiin

```
docker-compose exec app bash
```

### Tietokannan käyttö

PostgreSQL-tietokanta on käytettävissä Docker-kontin kautta. Voit yhdistää siihen joko suoraan portista 5432 tai konttien kautta:

```
docker-compose exec db psql -U postgres -d asuntoanalyysi
```

### Tuotantoversion rakentaminen

Tuotantoversiota varten on erillinen Dockerfile.prod:

```
docker build -f Dockerfile.prod -t asuntoanalyysi-prod .
```

## Julkaisu Render.com:issa

Sovellus voidaan julkaista Render.com-palvelussa käyttäen olemassa olevaa render.yaml-määrittelyä. 

Render.com käyttää PostgreSQL-tietokantaa, joka määritellään Render Dashboardissa. Tietokannan URL tulee asettaa ympäristömuuttujaan `DATABASE_URL`.

### Ympäristömuuttujat Render.com:issa

Aseta vähintään seuraavat ympäristömuuttujat Render.com:in dashboardissa:

- `FLASK_ENV`: production
- `SECRET_KEY`: Vahva satunnainen merkkijono
- `DATABASE_URL`: Render.com:in tarjoama PostgreSQL-URL
- `OPENAI_API_KEY`: OpenAI API-avain

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