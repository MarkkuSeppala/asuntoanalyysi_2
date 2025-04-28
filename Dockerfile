FROM python:3.11-slim

WORKDIR /app

# Kopioi riippuvuudet ja asenna ne
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install python-dotenv

# Kopioi sovellus
COPY . .

# Ympäristömuuttujat
ENV FLASK_APP=app.py
ENV FLASK_ENV=development
ENV PYTHONUNBUFFERED=1

# Portti
EXPOSE 5000

# Komento, joka suoritetaan kontin käynnistyessä
CMD ["flask", "run", "--host=0.0.0.0"] 