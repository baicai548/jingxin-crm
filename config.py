import os
class Config:
    SECRET_KEY = 'jingxin-crm-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///crm.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
