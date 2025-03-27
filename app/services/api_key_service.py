import os
import uuid
import json
import redis
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger
from app.models.api_key import ApiKey, ApiKeyCreate, ApiKeyInDB


class ApiKeyService:
    def __init__(self):
        # Initialize Redis connection
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", 6379))
        self.redis = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        # Key prefix for storing API keys
        self.key_prefix = "api_key:"
    
    def _generate_api_key(self) -> str:
        """Generate a unique API key"""
        return str(uuid.uuid4())
    
    def _generate_api_secret(self) -> str:
        """Generate a unique API secret"""
        return str(uuid.uuid4())
    
    async def create_api_key(self, api_key_data: ApiKeyCreate) -> ApiKey:
        """Create a new API key"""
        api_key = self._generate_api_key()
        api_secret = self._generate_api_secret()
        
        new_key = ApiKey(
            api_key=api_key,
            api_secret=api_secret,
            name=api_key_data.name,
            rate_limit=api_key_data.rate_limit,
            created_at=datetime.now(),
            is_active=True
        )
        
        # Store in Redis - use model_dump() which properly handles datetime serialization
        key_id = str(uuid.uuid4())
        self.redis.set(
            f"{self.key_prefix}{api_key}",
            json.dumps(new_key.model_dump(mode="json"))
        )
        
        # Also store by ID for listing all keys
        self.redis.set(
            f"{self.key_prefix}id:{key_id}",
            json.dumps(new_key.model_dump(mode="json"))
        )
        
        # Add to index of all keys
        self.redis.sadd("api_keys", key_id)
        
        return new_key
    
    async def validate_api_key(self, api_key: str, api_secret: str) -> Optional[ApiKey]:
        """Validate an API key and secret"""
        key_data = self.redis.get(f"{self.key_prefix}{api_key}")
        
        if not key_data:
            return None
        
        key_dict = json.loads(key_data)
        api_key_obj = ApiKey(**key_dict)
        
        if api_key_obj.api_secret != api_secret or not api_key_obj.is_active:
            return None
        
        return api_key_obj
    
    async def get_all_api_keys(self) -> List[ApiKey]:
        """Get all API keys"""
        key_ids = self.redis.smembers("api_keys")
        keys = []
        
        for key_id in key_ids:
            key_data = self.redis.get(f"{self.key_prefix}id:{key_id}")
            if key_data:
                keys.append(ApiKey(**json.loads(key_data)))
        
        return keys
    
    async def deactivate_api_key(self, api_key: str) -> bool:
        """Deactivate an API key"""
        key_data = self.redis.get(f"{self.key_prefix}{api_key}")
        
        if not key_data:
            return False
        
        key_dict = json.loads(key_data)
        key_dict["is_active"] = False
        
        self.redis.set(f"{self.key_prefix}{api_key}", json.dumps(key_dict))
        
        # Also update in the ID index
        for key_id in self.redis.smembers("api_keys"):
            id_key_data = self.redis.get(f"{self.key_prefix}id:{key_id}")
            if id_key_data:
                id_key_dict = json.loads(id_key_data)
                if id_key_dict.get("api_key") == api_key:
                    id_key_dict["is_active"] = False
                    self.redis.set(f"{self.key_prefix}id:{key_id}", json.dumps(id_key_dict))
                    break
        
        return True 