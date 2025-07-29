import os
from typing import List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings and configuration."""
    
    # Application
    APP_NAME: str = "Nexus Aggregator"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = "An intelligent information-gathering engine that transforms internet noise into structured signals"
    
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", 8000))
    DEBUG: bool = os.getenv("DEBUG", "True").lower() == "true"
    
    # API Keys
    API_KEYS: List[str] = [key.strip() for key in os.getenv("API_KEYS", "").split(",") if key.strip()]
    
    # External API Keys
    DEVTO_API_KEY: str = os.getenv("DEVTO_API_KEY", "9w")
    
    # Scraping
    DEFAULT_SCRAPING_LIMIT: int = int(os.getenv("DEFAULT_SCRAPING_LIMIT", 10))
    REQUEST_TIMEOUT: int = int(os.getenv("REQUEST_TIMEOUT", 10))
    
    # File paths
    SCRAPED_ARTICLES_DIR: str = os.getenv("SCRAPED_ARTICLES_DIR", "scraped_articles")
    LOGS_DIR: str = os.getenv("LOGS_DIR", "logs")
    
    # User Agent
    USER_AGENT: str = os.getenv(
        "USER_AGENT", 
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    )


# Create global settings instance
settings = Settings()
