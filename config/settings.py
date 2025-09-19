import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb+srv://lucas_db_user:2qUmqZWFrVRNSo0Y@cluster0.lynojhq.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'proyecto_final_db')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))

settings = Settings()
