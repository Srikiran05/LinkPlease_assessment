import os

class Config:
    API_KEY = 'bWFsbGFkaXNyaWtpcmFuQGdtYWlsLmNvbQ.7c14e383d729c7fcad6a'
    PSEUDOGRAM_BASE_URL = os.environ.get('PSEUDOGRAM_BASE_URL', 'https://pseudogram-api.onrender.com')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///linkplease.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
