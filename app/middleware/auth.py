from fastapi import Depends, HTTPException, Header
from fastapi.security import APIKeyHeader
from typing import Optional, Tuple
from loguru import logger
import os
from app.services.api_key_service import ApiKeyService
from app.models.api_key import ApiKey


api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
api_secret_header = APIKeyHeader(name="X-API-Secret", auto_error=False)
admin_secret_header = APIKeyHeader(name="X-Admin-Secret", auto_error=False)

api_key_service = ApiKeyService()


async def get_api_key(
    api_key: str = Depends(api_key_header),
    api_secret: str = Depends(api_secret_header)
) -> Tuple[str, ApiKey]:
    """
    Validate the API key and secret from the request headers
    Returns the API key and the API key object if valid
    """
    if not api_key or not api_secret:
        logger.warning("Missing API key or secret")
        raise HTTPException(
            status_code=401,
            detail="Missing API key or secret"
        )
    
    api_key_obj = await api_key_service.validate_api_key(api_key, api_secret)
    
    if not api_key_obj:
        logger.warning(f"Invalid API key: {api_key}")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key or secret"
        )
    
    logger.info(f"API key validated: {api_key} (name: {api_key_obj.name})")
    
    return api_key, api_key_obj


async def get_admin_secret(
    admin_secret: str = Depends(admin_secret_header)
) -> str:
    """
    Validate the admin secret from the request headers
    Returns the admin secret if valid
    """
    if not admin_secret:
        logger.warning("Missing admin secret")
        raise HTTPException(
            status_code=401,
            detail="Missing admin secret"
        )
    
    # Get API_SECRET_KEY from environment
    api_secret_key = os.getenv("API_SECRET_KEY")
    if not api_secret_key:
        logger.error("API_SECRET_KEY environment variable is not set")
        raise HTTPException(
            status_code=500,
            detail="Server configuration error"
        )
    
    if admin_secret != api_secret_key:
        logger.warning("Invalid admin secret")
        raise HTTPException(
            status_code=401,
            detail="Invalid admin secret"
        )
    
    logger.info("Admin secret validated")
    return admin_secret 