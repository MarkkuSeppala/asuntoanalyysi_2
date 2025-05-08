# Paytrail Maksujärjestelmä

Tämä moduuli tarjoaa integraation Paytrail-maksujärjestelmän kanssa. Järjestelmä mahdollistaa kertapakettien (3,90€, 5 analyysiä) ostamisen.

## Ominaisuudet

- Kertapakettien (5 analyysiä) ostaminen Paytrailin kautta
- Tuki eri maksutavoille (pankkimaksut, luottokortit, MobilePay, jne.)
- Maksun callback-käsittely
- Testausympäristön tuki

## Asennus ja konfigurointi

1. Asenna tarvittavat riippuvuudet:

```
pip install -r requirements.txt
```

2. Varmista, että tietokannassa on oikea tuote. Voit ajaa seuraavan skriptin:

```
python add_paytrail_product.py
```

3. Määritä Paytrail-tunnukset:

Tällä hetkellä käytössä on testitunnukset. Tuotantoympäristössä muokkaa `paytrail_service.py`-tiedostoa ja korvaa testitunnukset oikeilla tunnuksilla:

```python
# Paytrail test credentials
MERCHANT_ID = "375917"
SECRET_KEY = "SAIPPUAKAUPPIAS"
```

## Käyttö

### Asiakasnäkymä

1. Käyttäjä valitsee verkkokaupan puolella kertapaketin
2. Käyttäjä valitsee maksutavan (demo tai Paytrail)
3. Paytrail-maksutavalla käyttäjä ohjataan Paytrailin maksusivulle
4. Maksun jälkeen käyttäjä ohjataan takaisin sivustolle

### Kehittäjänäkymä

#### Maksun luominen

```python
from paytrail_service import create_payment

# Luo maksu
payment_data = create_payment(
    user_id=current_user.id,
    product=product,
    redirect_url_base="https://yoursite.com"
)

# Ohjaa käyttäjä maksusivulle
redirect(payment_data['payment_url'])
```

#### Maksun vahvistaminen

Maksun vahvistaminen tapahtuu automaattisesti callback-osoitteiden kautta. Callback-osoitteet ovat:

- Success: `/payment/callback/success`
- Cancel: `/payment/callback/cancel`

## Testaaminen

Paytrailin testiympäristössä voit käyttää seuraavia testitunnuksia:

- Merchant ID: `375917`
- Secret key: `SAIPPUAKAUPPIAS`

Testitunnuksia käyttäessäsi voit simuloida maksuja ilman oikeaa rahaliikennettä.

### Eri maksutyyppien testaus

Paytrailin testiympäristössä kaikki maksutavat eivät ole tuettuja. Voit testata seuraavia maksutapoja:

#### Verkkopankit
- Nordea
- OP

#### Kortit
- Visa
- Mastercard

## Vianetsintä

### Yleiset ongelmat

**Virhe: Invalid signature**
- Tarkista, että käytät oikeita tunnuksia
- Varmista, että signature-laskenta on oikein

**Virhe: API-kutsu ei onnistu**
- Tarkista verkkoyhteytesi
- Varmista, että Paytrailin API-palvelu on saatavilla

## Tuotantoon siirtyminen

Tuotantoon siirtyessä:

1. Hanki oikeat Paytrail-tunnukset
2. Päivitä tunnukset `paytrail_service.py`-tiedostoon
3. Testaa maksuprosessi kehitysympäristössä
4. Varmista, että callback-osoitteet ovat oikein konfiguroitu tuotantoympäristössä

## Turvallisuus

- Callback-osoitteiden allekirjoitusten tarkistus on toteutettu `verify_payment_signature`-funktiossa
- SSL-yhteys on pakollinen tuotantokäytössä
- Käyttäjätietoja ei tallenneta Paytrailin järjestelmään 