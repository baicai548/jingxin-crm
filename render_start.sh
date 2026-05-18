
#!/usr/bin/env bash
python -c "
import os, sys
sys.path.insert(0, '.')
os.environ.setdefault('DATABASE_URL', '')
database_url = os.environ.get('DATABASE_URL', '')
if database_url.startswith('postgres://'):
    os.environ['DATABASE_URL'] = database_url.replace('postgres://', 'postgresql://', 1)
from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
    print('Tables recreated!')
"
gunicorn app:app --bind 0.0.0.0:$PORT
