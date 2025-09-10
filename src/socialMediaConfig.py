"""
Configuration management for social media jobs
Handles all API keys, database connections, and settings securely
"""
import os
from typing import Dict
from dataclasses import dataclass
from pymongo import MongoClient
import logging

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, try to load manually
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value


@dataclass
class DatabaseConfig:
    """Database configuration"""
    uri: str
    db_name: str
    collections: Dict[str, str]

@dataclass
class APIConfig:
    """API configuration"""
    youtube_api_key: str
    twitter_bearer_token: str
    apify_api_token: str
    apify_actor_id: str


@dataclass
class AppConfig:
    """Application configuration"""
    max_results: int = 100
    retry_attempts: int = 3
    retry_delay: int = 60
    rate_limit_delay: int = 2
    log_level: str = "INFO"


class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.loadFromEnv()
        self.setupLogging()
    
    def loadFromEnv(self):
        """Load configuration from environment variables"""
        # Database configuration
        self.database = DatabaseConfig(
            uri=os.getenv('MONGO_URI', 'mongodb://localhost:27017/'),
            db_name=os.getenv('DB_NAME', 'smFeeds'),
            collections={
                'search_keywords': os.getenv(
                    'SEARCH_KEYWORDS_COLLECTION', 'searchKeywords'
                ),
                'youtube': os.getenv('YOUTUBE_COLLECTION', 'youtube'),
                'facebook': os.getenv('FACEBOOK_COLLECTION', 'facebook'),
                'xtweets': os.getenv('XTWEETS_COLLECTION', 'xtweets'),
                'youtube_with_channel': os.getenv(
                    'YOUTUBE_WITH_CHANNEL_COLLECTION', 'youtubeWithChannel'
                )
            }
        )
        
        # API configuration
        self.api = APIConfig(
            youtube_api_key=os.getenv('YOUTUBE_API_KEY'),
            twitter_bearer_token=os.getenv('TWITTER_BEARER_TOKEN'),
            apify_api_token=os.getenv('APIFY_API_TOKEN'),
            apify_actor_id=os.getenv('APIFY_ACTOR_ID', 'facebook-search-task')
        )
        
        # Application configuration
        self.app = AppConfig(
            max_results=int(os.getenv('MAX_RESULTS', '100')),
            retry_attempts=int(os.getenv('RETRY_ATTEMPTS', '3')),
            retry_delay=int(os.getenv('RETRY_DELAY', '60')),
            rate_limit_delay=int(os.getenv('RATE_LIMIT_DELAY', '2')),
            log_level=os.getenv('LOG_LEVEL', 'INFO')
        )
        
        # Validate required settings
        self.validateConfig()
    
    def validateConfig(self):
        """Validate that required configuration is present"""
        required_api_keys = [
            ('YOUTUBE_API_KEY', self.api.youtube_api_key),
            ('TWITTER_BEARER_TOKEN', self.api.twitter_bearer_token),
            ('APIFY_API_TOKEN', self.api.apify_api_token)
        ]
        
        missing_keys = []
        for key_name, key_value in required_api_keys:
            if not key_value or key_value.startswith('your_'):
                missing_keys.append(key_name)
        
        if missing_keys:
            # Log warning instead of raising error for testing
            import logging
            logging.warning(
                f"Missing or placeholder environment variables: {', '.join(missing_keys)}"
            )
            logging.warning("Please update your .env file with actual API keys")
    
    def setupLogging(self):
        """Setup logging configuration"""
        from pathlib import Path
        from datetime import datetime
        
        # Log to home directory
        home_dir = Path.home()
        log_file = home_dir / f'social_media_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        
        logging.basicConfig(
            level=getattr(logging, self.app.log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
    
    def getMongoClient(self) -> MongoClient:
        """Get MongoDB client with proper error handling"""
        try:
            client = MongoClient(self.database.uri)
            # Test connection
            client.admin.command('ping')
            return client
        except Exception as e:
            logging.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def getCollection(self, collectionName: str):
        """Get a specific collection from the database"""
        client = self.getMongoClient()
        db = client[self.database.db_name]
        return db[collectionName]


# Global config instance
config = Config()
