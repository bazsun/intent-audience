"""MongoDB client and connection management."""

from typing import Optional, Dict, Any, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
import logging

from ..config.settings import settings

logger = logging.getLogger(__name__)


class MongoClient:
    """MongoDB connection manager."""
    
    def __init__(self):
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._connection_url = settings.mongodb_url
        self._db_name = "intent_audience"
    
    async def initialize(self) -> None:
        """Initialize MongoDB connection."""
        if self._client is not None:
            logger.warning("MongoDB client already initialized")
            return
            
        try:
            self._client = AsyncIOMotorClient(self._connection_url)
            self._database = self._client[self._db_name]
            
            # Test connection
            await self._client.admin.command('ping')
            logger.info("MongoDB connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB connection: {e}")
            raise
    
    async def close(self) -> None:
        """Close MongoDB connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            logger.info("MongoDB connection closed")
    
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection:
        """Get a MongoDB collection."""
        if not self._database:
            raise RuntimeError("MongoDB not initialized. Call initialize() first.")
        return self._database[collection_name]
    
    async def insert_one(self, collection_name: str, document: Dict[str, Any]) -> str:
        """Insert a single document."""
        collection = self.get_collection(collection_name)
        result = await collection.insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, collection_name: str, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents."""
        collection = self.get_collection(collection_name)
        result = await collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    async def find_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        collection = self.get_collection(collection_name)
        return await collection.find_one(filter_dict)
    
    async def find_many(
        self, 
        collection_name: str, 
        filter_dict: Dict[str, Any] = None,
        limit: int = None,
        skip: int = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        collection = self.get_collection(collection_name)
        cursor = collection.find(filter_dict or {})
        
        if skip:
            cursor = cursor.skip(skip)
        if limit:
            cursor = cursor.limit(limit)
            
        return await cursor.to_list(length=limit)
    
    async def update_one(
        self, 
        collection_name: str, 
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any]
    ) -> bool:
        """Update a single document."""
        collection = self.get_collection(collection_name)
        result = await collection.update_one(filter_dict, {"$set": update_dict})
        return result.modified_count > 0
    
    async def delete_one(self, collection_name: str, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document."""
        collection = self.get_collection(collection_name)
        result = await collection.delete_one(filter_dict)
        return result.deleted_count > 0
    
    async def count_documents(self, collection_name: str, filter_dict: Dict[str, Any] = None) -> int:
        """Count documents in collection."""
        collection = self.get_collection(collection_name)
        return await collection.count_documents(filter_dict or {})
    
    async def health_check(self) -> bool:
        """Check if MongoDB connection is healthy."""
        try:
            await self._client.admin.command('ping')
            return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
            return False


# Global client instance
mongo_client = MongoClient()