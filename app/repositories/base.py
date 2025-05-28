from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

T = TypeVar('T')

class BaseRepository(Generic[T], ABC):
    """Base repository interface that defines the contract for all repositories"""
    
    @abstractmethod
    async def get_all(self) -> List[T]:
        """Get all items"""
        pass
    
    @abstractmethod
    async def get_by_id(self, id: str) -> Optional[T]:
        """Get item by id"""
        pass
    
    @abstractmethod
    async def create(self, item: T) -> T:
        """Create new item"""
        pass
    
    @abstractmethod
    async def update(self, id: str, item: T) -> Optional[T]:
        """Update existing item"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Delete item"""
        pass 