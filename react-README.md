# AsuntoAnalyysi React Frontend

Tämä on AsuntoAnalyysi-sovelluksen React-pohjainen frontend-toteutus. 

## React-buildin esivalmistelu

Ennen kuin pusketaan sovellus Render.com palveluun, täytyy React-sovellus buildata paikallisesti. Tämä johtuu siitä, että Render.com samaan tilaan täytyy saada sekä Flask-backend että React-frontend.

### Buildaus-ohjeet

1. Asenna Node.js (version 14 tai uudempi)
2. Asenna tarvittavat riippuvuudet:
   ```
   npm install
   ```
3. Buildaa React-sovellus:
   ```
   npm run build
   ```
4. Varmista että build-kansio on luotu projektin juureen
5. Pushaa koko projekti (mukaan lukien build-kansio) Render.com:in

### Mitä tapahtuu Render.com palvelussa

1. `build.sh` skripti havaitsee build-kansion olemassaolon
2. Skripti kopioi build-hakemiston sisällön static/react-hakemistoon
3. Flask-sovellus tarjoilee staattisia tiedostoja sijainnista `/static/react/`
4. React-sovellus on saatavilla osoitteessa `/react`

## Kehittäminen

Kehitystilassa React-sovellusta voidaan ajaa komennolla:

```
npm start
```

Tällöin React-sovellus käynnistyy oletuksena osoitteeseen `http://localhost:3000` ja tekee API-kutsut osoitteeseen `http://localhost:5000`.

## Tuotantoympäristö

Tuotantoympäristössä kaikki API-kutsut tehdään samaan origiin, jossa itse React-sovellus on (eli `/api/...` polut). Tämän ansiosta ei tarvita erillistä konfigurointia CORS-asetuksiin. 