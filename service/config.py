import os

class Config:
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_NAME = os.getenv('DB_NAME', 'user_management')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'karthickraj5')
    DB_PORT = os.getenv('DB_PORT', '5432')
    
    @property
    def DATABASE_URL(self):
        return f"dbname='{self.DB_NAME}' user='{self.DB_USER}' password='{self.DB_PASSWORD}' host='{self.DB_HOST}' port='{self.DB_PORT}'"

config = Config()