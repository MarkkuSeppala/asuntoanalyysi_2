# Salaisuuksien poistaminen Git-historiasta

Tämä ohje auttaa poistamaan arkaluontoiset tiedot (kuten API-avaimet ja salaisuudet) Git-historiasta.

## Vaihtoehdot

GitHub antaa kaksi vaihtoehtoa:

1. **Salli tunnistetut salaisuudet** - käytä GitHubin tarjoamia linkkejä merkitäksesi salaisuudet turvallisiksi.
   - Helppo, mutta **ei suositeltava**, koska salaisuudet jäävät historiaan.
   - Linkit: GitHubin virheilmoituksessa mainitut osoitteet

2. **Poista salaisuudet historiasta** - turvallisempi, mutta vaativampi vaihtoehto.
   - Tässä vaiheittainen ohje:

## Git-historian puhdistaminen salaisuuksista

### 1. Varmuuskopiointi

Luo uusi branch varmuuskopioksi:
```bash
git checkout -b backup-before-cleanup
git checkout main
```

### 2. Käytä BFG Repo-Cleaner -työkalua

BFG on tehokas työkalu Git-repositorion puhdistamiseen.

1. Lataa BFG: [https://rtyley.github.io/bfg-repo-cleaner/](https://rtyley.github.io/bfg-repo-cleaner/)

2. Luo tiedosto `secrets.txt` seuraavalla sisällöllä:
```
299087554173-nr6kp1jlb0gqqdn7hdkn6dsndbma467h.apps.googleusercontent.com=***REMOVED***
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=***REMOVED***
```

3. Suorita BFG-komento:
```bash
java -jar bfg.jar --replace-text secrets.txt .
```

### 3. Puhdista ja pakota push

Puhdista Git-tietokanta ja pakota muutokset etärepositorioon:

```bash
git reflog expire --expire=now --all
git gc --prune=now --aggressive
git push --force-with-lease origin main
```

## Vaihtoehtoinen tapa: Git filter-repo

Jos BFG ei ole käytettävissä, voit käyttää Git filter-repo -työkalua:

1. Asenna työkalu:
```bash
pip install git-filter-repo
```

2. Puhdista repository:
```bash
git filter-repo --replace-text expressions.txt
```

Missä `expressions.txt` sisältää:
```
299087554173-nr6kp1jlb0gqqdn7hdkn6dsndbma467h.apps.googleusercontent.com=REMOVED_CLIENT_ID
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=REMOVED_CLIENT_SECRET
```

### Huomioitavaa:

- Historian muuttaminen on peruuttamaton toimenpide
- Kaikki tiimin jäsenet joutuvat kloonaamaan repositorion uudelleen tai tekemään muita toimenpiteitä
- Tiedota muutoksesta kaikille, joilla on pääsy repositorioon 