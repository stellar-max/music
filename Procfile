# Procfile - Auto-detected by Heroku
web: gunicorn --worker-class eventlet -w 1 app:app

# For background processes (optional)
worker: python bot.py

# For scheduled tasks (optional)
clock: python scheduler.py
