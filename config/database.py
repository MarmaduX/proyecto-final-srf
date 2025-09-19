from pymongo import MongoClient
from .settings import settings

class DatabaseConfig:
    def __init__(self):
        self.mongo_uri = settings.MONGODB_URI
        self.database_name = settings.DATABASE_NAME
        self.client = None
        self.db = None
    
    def connect(self):
        try:
            self.client = MongoClient(self.mongo_uri)
            self.db = self.client[self.database_name]
            self.client.admin.command('ping')
            print(f"Connected to MongoDB: {self.database_name}")
            return True
        except Exception as e:
            print(f"Failed to connect to MongoDB: {e}")
            return False
    
    def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB")
    
    def get_collection(self, collection_name):
        if self.db is not None:
            return self.db[collection_name]
        return None

db_config = DatabaseConfig()
