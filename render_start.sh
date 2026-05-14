#!/bin/bash
python -c "from app import app; from models import db; app.app_context().push(); db.create_all(); print('DB OK')"
gunicorn app:app --bind 0.0.0.0:$PORT