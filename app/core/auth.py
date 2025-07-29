import os
from typing import List, Optional
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Security scheme for API key authentication
security_scheme = HTTPBearer()


class APIKeyAuth:
    def __init__(self):
        # Load valid API keys from environment
        api_keys_str = os.getenv("API_KEYS", "")
        self.valid_api_keys = [key.strip() for key in api_keys_str.split(",") if key.strip()]
        
        if not self.valid_api_keys:
            raise ValueError("No API keys found in environment variables")
    
    def validate_api_key(self, credentials: HTTPAuthorizationCredentials = Security(security_scheme)) -> str:
        """
        Validate the provided API key.
        
        Args:
            credentials: The HTTP authorization credentials
            
        Returns:
            str: The validated API key
            
        Raises:
            HTTPException: If the API key is invalid
        """
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="API key is required",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        api_key = credentials.credentials
        
        if api_key not in self.valid_api_keys:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return api_key


# Create a global instance
api_key_auth = APIKeyAuth()
