#!/usr/bin/env bash
python -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('Tables ready!')
"
gunicorn app:app --bind 0.0.0.0:$PORT
