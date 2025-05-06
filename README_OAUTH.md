# Google OAuth-integraation asennus

Tämä dokumentti selittää, miten Google OAuth-integraatio asennetaan ja konfiguroidaan tuotantoympäristössä.

## Ympäristömuuttujat

Turvallisuussyistä OAuth-salaisuudet tulee asettaa ympäristömuuttujiin koodiin hardkoodaamisen sijaan. Aseta seuraavat ympäristömuuttujat:

```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://www.your-domain.com/login/google/authorized
```

### Ympäristömuuttujien asettaminen Dockerissa

1. Lisää ympäristömuuttujat docker-compose.yml tiedostoon:

```yaml
services:
  web:
    # ... muut asetukset ...
    environment:
      - GOOGLE_CLIENT_ID=your-google-client-id
      - GOOGLE_CLIENT_SECRET=your-google-client-secret
      - GOOGLE_REDIRECT_URI=https://www.your-domain.com/login/google/authorized
      # ... muut ympäristömuuttujat ...
```

Vaihtoehtoisesti, voit käyttää .env-tiedostoa:

1. Luo `.env` tiedosto projektin juureen (varmista, että se on .gitignore-tiedostossa):

```
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://www.your-domain.com/login/google/authorized
```

2. Lisää `.env` tiedosto docker-compose.yml konfiguraatioon:

```yaml
services:
  web:
    # ... muut asetukset ...
    env_file:
      - .env
```

### Ympäristömuuttujien asettaminen Renderissä

1. Mene Render-palvelun hallintapaneeliin
2. Valitse sovelluksesi
3. Mene "Environment" -välilehdelle
4. Lisää seuraavat ympäristömuuttujat:
   - `GOOGLE_CLIENT_ID`: Google Client ID
   - `GOOGLE_CLIENT_SECRET`: Google Client Secret
   - `GOOGLE_REDIRECT_URI`: https://your-render-app.onrender.com/login/google/authorized

## Tietokannan päivitys

Jotta OAuth-integraatio toimii, tietokantarakenne täytyy päivittää. Tämä voidaan tehdä kahdella tavalla:

### 1. Käyttäen Flask-Migrate:

```bash
# Renderissä Shell-konsolissa:
flask db upgrade

# Dockerissa:
docker-compose exec web flask db upgrade
```

### 2. Käyttäen update_db_oauth.py -skriptiä:

```bash
# Renderissä Shell-konsolissa:
python update_db_oauth.py

# Dockerissa:
docker-compose exec web python update_db_oauth.py
```

## Google Cloud Console -asetukset

1. Mene [Google Cloud Console](https://console.cloud.google.com/)
2. Valitse projektisi
3. Mene "APIs & Services" > "Credentials"
4. Muokkaa OAuth 2.0 Client ID asetuksia
5. Lisää "Authorized redirect URIs" -kohtaan:
   - Tuotanto: https://www.your-domain.com/login/google/authorized
   - Kehitys: http://localhost:5000/login/google/authorized
   
6. Tallenna muutokset

## Ongelmatilanteet

Jos kohtaat ongelmia OAuth-integraation kanssa, tarkista seuraavat asiat:

1. Ympäristömuuttujat on asetettu oikein
2. Tietokanta on päivitetty (tarkista että `oauth`-taulu on olemassa)
3. Google Cloud Console -asetuksissa redirect URI on oikein
4. Lokitiedostoista mahdolliset virheviestit 