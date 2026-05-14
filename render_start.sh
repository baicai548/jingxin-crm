#!/bin/bash
python -c "
from app import app
from models import db
with app.app_context():
    db.create_all()
    print('DB OK')
"
gunicorn app:app --bind 0.0.0.0:$PORT
