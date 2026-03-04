"""
Authentication module for SURA eligibility API.

Provides simple API key-based authentication for internal use.
"""

import logging
from typing import Optional
from fastapi import Header, HTTPException, status

from config.settings import get_settings

logger = logging.getLogger(__name__)


async def verify_api_key(
    x_sura_api_key: Optional[str] = Header(None, alias="X-SURA-API-Key")
) -> str:
    """
    Verify API key from request header.
    
    Args:
        x_sura_api_key: API key from X-SURA-API-Key header
        
    Returns:
        Validated API key
        
    Raises:
        HTTPException: If API key is missing or invalid
    """
    if not x_sura_api_key:
        logger.warning("API key missing in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key is required. Please provide X-SURA-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    settings = get_settings()
    
    # Get valid API keys from settings
    valid_keys = []
    if hasattr(settings, 'sura_internal_keys'):
        valid_keys = settings.sura_internal_keys.split(',')
        valid_keys = [key.strip() for key in valid_keys if key.strip()]
    
    if not valid_keys:
        logger.error("No SURA API keys configured in settings")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="API authentication not properly configured"
        )
    
    # Validate API key
    if x_sura_api_key not in valid_keys:
        logger.warning(f"Invalid API key attempt: {x_sura_api_key[:8]}...")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "ApiKey"}
        )
    
    logger.debug(f"API key validated successfully: {x_sura_api_key[:8]}...")
    return x_sura_api_key
