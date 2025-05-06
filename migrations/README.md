# Tietokantamigraatioiden hallinta

Tämä hakemisto sisältää tietokantamigraatiot ja työkalut, joilla hallitaan sovelluksen eri tietokantojen rakennetta.

## Migraatioiden tarkoitus

Migraatioiden avulla voit:
1. Pitää useita tietokantoja samassa rakenteessa (kehitys, testaus, tuotanto)
2. Hallita tietokantamuutoksia versionhallinnassa
3. Suorittaa tietokantamuutokset helposti eri ympäristöissä
4. Perua muutoksia tarvittaessa

## Työkalun käyttö

### Asennus

Varmista, että olet asentanut tarvittavat riippuvuudet:

```bash
pip install -r requirements.txt
```

### Migraatioympäristön alustus

Kun otat migraatiot käyttöön ensimmäistä kertaa, alusta migraatioympäristö:

```bash
python migrations/manage_migrations.py init
```

### Uuden migraation luominen

Kun teet muutoksia models.py-tiedostoon (lisäät uusia malleja tai muokkaat olemassa olevia), luo uusi migraatio:

```bash
python migrations/manage_migrations.py migrate "Migraation kuvaus"
```

Tämä luo uuden migraatiotiedoston versions-hakemistoon. Tarkista tiedosto ja varmista, että se sisältää haluamasi muutokset.

### Migraatioiden suorittaminen

Kun haluat päivittää tietokannan rakenteen viimeisimpään versioon:

```bash
python migrations/manage_migrations.py upgrade
```

Suorita tämä komento kaikissa ympäristöissä (kehitys, testaus, tuotanto) saadaksesi samat muutokset käyttöön kaikkialla.

## Eri ympäristöjen hallinta

Voit käyttää eri tietokantoja eri ympäristöissä asettamalla `DATABASE_URL`-ympäristömuuttujan:

```bash
# Kehitysympäristö (paikallinen SQLite)
DATABASE_URL="sqlite:///flask_database.db" python migrations/manage_migrations.py upgrade

# Toinen kehitysympäristö
DATABASE_URL="sqlite:///toinen_kehitys.db" python migrations/manage_migrations.py upgrade

# Tuotantoympäristö (Render.com PostgreSQL)
DATABASE_URL="postgresql://user:password@host:port/dbname" python migrations/manage_migrations.py upgrade
```

## Tuotantokäyttö

Renderissä voit suorittaa migraatiot osana build-vaihetta tai erillisenä komentona. Lisää esimerkiksi seuraava komento Render.com:in Build Command -kenttään:

```bash
pip install -r requirements.txt && python migrations/manage_migrations.py upgrade
```

## Migraatioiden peruminen

Jos tarvitset perua migraation, voit käyttää `downgrade`-komentoa (tämä vaatii erikseen toteutettavan downgrade-tuen migraatioskriptiin). 