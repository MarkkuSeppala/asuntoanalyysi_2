# Tilausjärjestelmä (Subscription System)

Tämä dokumentti kuvaa automaattisesti uusiutuvien tilausten toimintaa sovelluksessa.

## Yleiskuvaus

Koska Paytrail ei tarjoa suoraa API-tukea uusiutuville maksuille, järjestelmä on toteutettu siten, että se hoitaa tilausten uusinnan automaattisesti sovelluksessa. Järjestelmä seuraa tilauskausien päättymistä ja luo uuden maksun tilauksille, jotka ovat uusiutumassa.

## Moduulit ja rakenne

### 1. Subscription Service (subscription_service.py)

Tämä moduuli sisältää kaikki tilauksiin liittyvät toiminnot:

- Tilauksen luominen
- Tilauksen peruuttaminen
- Tilauksen uusiminen
- Uusiutuvien maksujen käsittely
- Uusiutuvien tilausten hakeminen

### 2. Subscription Scheduler (subscription_scheduler.py)

Tämä moduuli vastaa ajastettujen tehtävien suorittamisesta:

- Tilausten uusiminen automaattisesti ennen päättymistä
- Muistutusten lähettäminen käyttäjille
- Epäonnistuneiden maksujen käsittely
- Päättyneiden tilausten merkitseminen

### 3. Email Service (email_service.py)

Tilaussähköpostien lähettämiseen lisätyt funktiot:

- Tilauksen uusimissähköpostit
- Muistutussähköpostit
- Epäonnistuneen maksun viestit
- Tilauksen päättymisviestit

### 4. Subscription CLI (subscription_cli.py)

Komentorivityökalu tilausten hallintaan:

- Tilausten listaus
- Manuaalinen tilausten uusiminen
- Tilausten peruuttaminen
- Uusimisprosessin manuaalinen käynnistäminen
- Scheduler-prosessin käynnistäminen

## Tietokantataulut

Tilausjärjestelmä käyttää seuraavia tietokantatauluja:

- **Subscription**: Tilausten tiedot
- **Payment**: Maksutiedot
- **Product**: Tuotetiedot

## Tilauksen elinkaari

1. **Uusi tilaus**
   - Käyttäjä tilaa tuotteen
   - Luodaan `Payment`-tietue (status: pending)
   - Käyttäjä maksaa tilauksen Paytrail-palvelussa
   - Maksun onnistuessa luodaan `Subscription`-tietue (status: active)

2. **Tilauksen uusiminen**
   - Scheduler tarkistaa päivittäin uusittavat tilaukset
   - Tilaukselle luodaan uusi `Payment`-tietue
   - Käyttäjälle lähetetään sähköposti maksulinkillä
   - Käyttäjä maksaa uusimismaksun Paytrail-palvelussa
   - Tilaus merkitään uusituksi ja päättymispäivää jatketaan

3. **Tilauksen peruuttaminen**
   - Käyttäjä voi peruuttaa tilauksen välittömästi tai kauden päätteeksi
   - Välitön peruutus: tilaus merkitään peruutetuksi heti
   - Kauden päätteeksi: tilaus merkitään peruutettavaksi kauden lopussa

4. **Tilauksen päättyminen**
   - Scheduler tarkistaa päivittäin päättyneet tilaukset
   - Päättyneet tilaukset merkitään päättyneiksi (status: expired/cancelled)
   - Käyttäjälle lähetetään ilmoitus tilauksen päättymisestä

## Schedulerin käynnistäminen

Scheduler käynnistyy automaattisesti tuotantoympäristössä, kun sovellus käynnistyy. Kehitysympäristössä schedulerin voi käynnistää manuaalisesti:

```
python subscription_cli.py run-scheduler
```

Vaihtoehtoisesti schedulerin voi pakottaa käynnistymään myös kehitysympäristössä asettamalla ympäristömuuttujan:

```
RUN_SUBSCRIPTION_SCHEDULER=true
```

## Manuaaliset toimenpiteet

Tilauksia voi hallita manuaalisesti komentorivityökalulla:

- Tilausten listaus: `python subscription_cli.py list`
- Tilauksen uusiminen: `python subscription_cli.py renew <id>`
- Tilauksen peruuttaminen: `python subscription_cli.py cancel <id>`
- Päättyvien tilausten listaus: `python subscription_cli.py expiring --days 7`
- Uusintaprosessin manuaalinen käynnistys: `python subscription_cli.py process` 