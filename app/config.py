import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'sahil-secret-key-2024')
    
    # Direct PostgreSQL Configuration
    DB_NAME = "Old_Age_Management_System_db"
    DB_USER = "postgres"
    DB_PASSWORD = "sahil@1234"
    DB_HOST = "localhost"
    DB_PORT = "5432"    

    @staticmethod
    def get_db_connection():
        import psycopg2
        return psycopg2.connect(
            dbname=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT
        )
