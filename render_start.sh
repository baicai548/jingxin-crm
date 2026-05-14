#!/bin/bash
python -c "
from app import app
from models import db
with app.app_context():
    db.drop_all()
    db.create_all()
    print('DB Reset OK')
"
gunicorn app:app --bind 0.0.0.0:$PORT
