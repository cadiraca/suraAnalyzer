"""Thread-safe singleton client manager for Gemini connections."""

import threading
import time
import logging
from typing import Optional
from src.api.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class ClientManager:
    """Thread-safe singleton manager for GeminiClient instances."""
    
    _instance: Optional['ClientManager'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        self._client: Optional[GeminiClient] = None
        self._client_lock = threading.Lock()
        self._last_health_check = 0
        self._health_check_interval = 300  # 5 minutes
    
    @classmethod
    def get_instance(cls) -> 'ClientManager':
        """Get singleton instance with double-checked locking."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
                    logger.info("Created new ClientManager singleton instance")
        return cls._instance
    
    def get_client(self) -> GeminiClient:
        """Get or create GeminiClient with health check."""
        with self._client_lock:
            current_time = time.time()
            
            # Create client if none exists
            if self._client is None:
                logger.info("Initializing new GeminiClient")
                self._client = GeminiClient()
                self._last_health_check = current_time
                return self._client
            
            # Perform periodic health check
            if current_time - self._last_health_check > self._health_check_interval:
                if self._client.is_healthy():
                    self._last_health_check = current_time
                    logger.debug("Client health check passed")
                else:
                    logger.warning("Client health check failed, recreating client")
                    self._client = GeminiClient()
                    self._last_health_check = current_time
            
            return self._client
    
    def reset_client(self):
        """Reset client connection (for error recovery)."""
        with self._client_lock:
            logger.info("Resetting GeminiClient connection")
            self._client = None
    
    def shutdown(self):
        """Cleanup resources on shutdown."""
        with self._client_lock:
            if self._client:
                logger.info("Shutting down GeminiClient")
                self._client = None


# Global instance accessor
def get_gemini_client() -> GeminiClient:
    """Get shared GeminiClient instance."""
    return ClientManager.get_instance().get_client()
