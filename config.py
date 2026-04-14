# config.py - Configuration settings
import os

class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SECRET_KEY = 'your-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "instance", "farmers.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ITEMS_PER_PAGE = 50
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB for bulk upload
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
    
    # Allowed file extensions for upload
    ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

class DevelopmentConfig(Config):
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

# Select config based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}