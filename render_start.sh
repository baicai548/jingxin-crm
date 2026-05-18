#!/usr/bin/env bash
python -c "
from app import app, db
app.app_context().push()
db.drop_all()
db.create_all()
print('Tables recreated!')
"
gunicorn app:app --bind 0.0.0.0:$PORT
