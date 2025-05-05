# PDF-tietojen poimintaohje

Tämä ominaisuus korvaa `kat_api_call.py` toiminnallisuuden ja käyttää nyt PDF-tiedostojen käsittelyä OpenAI API:n sijasta.

## Toiminnallisuus

`info_extract.py` poimii PDF-tiedostoista seuraavat tiedot ja tallentaa ne tietokantaan:

- **osoite**: Kohteen katu ja osoite
- **tyyppi**: Rakennuksen tyyppi (omakotitalo, kerrostalo, rivitalo, jne.)
- **hinta**: Ensisijaisesti velaton hinta, toissijaisesti myyntihinta
- **rakennusvuosi**: Kohteen rakennusvuosi
- **neliot**: Asuinpinta-ala neliömetreinä
- **huoneet**: Huoneiden lukumäärä

## Käyttöohjeet

### Tietokannan päivitys

Jos käytät olemassa olevaa tietokantaa, suorita ensin migraatioskripti lisätäksesi uudet sarakkeet:

```bash
python migrations/add_neliot_huoneet.py
```

### Yksittäisen PDF-tiedoston käsittely

```bash
python info_extract.py polku/tiedostoon.pdf [output.json] [kaupunki]
```

- **polku/tiedostoon.pdf**: Pakollinen. Polku käsiteltävään PDF-tiedostoon
- **output.json**: Valinnainen. JSON-tiedosto johon tiedot tallennetaan (oletus: "oikotie.json")
- **kaupunki**: Valinnainen. Kaupungin nimi (oletus: "Tuntematon")

### Kansion käsittely

Muokkaa tiedostoa info_extract.py ja muuta kansio-muuttujaa:

```python
kansio = "D:/OIKOTIE LATAUKSET/testi"  # pääkansio, jossa alikansioita
json_output = "oikotie.json"
```

Suorita sitten skripti ilman parametreja:

```bash
python info_extract.py
```

### Käyttö ohjelmassa

Käytä `process_single_pdf`-funktiota sovelluksestasi:

```python
from info_extract import process_single_pdf

# Käsittele PDF-tiedosto ja tallenna tiedot tietokantaan
result = process_single_pdf(
    pdf_path="polku/tiedostoon.pdf", 
    output_json_path="tiedot.json",
    kaupunki_nimi="Helsinki",
    analysis_id=1,  # Liittyy tähän analyysiin
    user_id=2       # Käyttäjän ID
)

if result and result.get("kohde_id"):
    print(f"Tiedot tallennettu, kohde_id: {result.get('kohde_id')}")
```

## Riippuvuudet

Asenna tarvittavat riippuvuudet:

```bash
pip install pdfplumber
```

## Huomioitavaa

- Skripti käsittelee PDF-tiedostoja pääkansiossa ja sen alikansioissa
- Alikansioiden nimiä käytetään kaupungin nimenä
- Tiedot tallennetaan sekä JSON-tiedostoon että tietokantaan 