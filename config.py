import os

class Config:
    SECRET_KEY = 'jingxin-crm-secret-key-2026'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///crm.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 百度OCR配置
    BAIDU_OCR_API_KEY = 'XABbET6H7QZWCMUsAiaemG0t'
    BAIDU_OCR_SECRET_KEY = '8b3k65e69Q13VWbPJAlyL047B1Zs9FN2'
