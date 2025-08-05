"""
Configuration settings for the Resume Evaluator application
"""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-change-this-in-production')
    
    # Database Configuration (Supabase/PostgreSQL)
    SUPABASE_URL = os.getenv('SUPABASE_URL')
    SUPABASE_KEY = os.getenv('SUPABASE_KEY')
    SUPABASE_ANON_KEY = os.getenv('SUPABASE_ANON_KEY')
    
    # Legacy MySQL Configuration (for migration)
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DB = os.getenv('MYSQL_DB', 'resume_evaluator')
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Database Type Selection
    DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'supabase')  # 'supabase' or ssds'mysql'
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_FILE_SIZE_MB', 16)) * 1024 * 1024  # 16MB default
    ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
    MAX_RESUMES_PER_BATCH = int(os.getenv('MAX_RESUMES_PER_BATCH', 50))
    
    # AI Configuration
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    AI_TEMPERATURE = float(os.getenv('AI_TEMPERATURE', 0.1))
    AI_MAX_TOKENS = int(os.getenv('AI_MAX_TOKENS', 4000))
    AI_TIMEOUT = int(os.getenv('AI_TIMEOUT', 300))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def init_app(app):
        """Initialize application with configuration"""
        # Create upload folder if it doesn't exist
        os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Override with more secure defaults for production
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("FLASK_SECRET_KEY must be set in production")

class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = True
    TESTING = True
    MYSQL_DB = os.getenv('MYSQL_TEST_DB', 'resume_evaluator_test')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}