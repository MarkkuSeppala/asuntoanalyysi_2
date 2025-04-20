#!/bin/bash
set -e

echo "Asetetaan tuotantoympäristö..."
export PRODUCTION=true

# Määritetään työntekijöiden määrä käytettävissä olevien CPU-ytimien mukaan
WORKERS=$(nproc 2>/dev/null || echo 4)

echo "Käynnistetään gunicorn $WORKERS työntekijällä..."
gunicorn app:app \
    --workers=$WORKERS \
    --bind=0.0.0.0:$PORT \
    --access-logfile=- \
    --error-logfile=- \
    --log-level=info