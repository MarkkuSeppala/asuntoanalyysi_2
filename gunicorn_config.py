# Gunicorn konfiguraatio
timeout = 300  # 5 minuuttia
workers = 2
threads = 2
bind = "0.0.0.0:$PORT"