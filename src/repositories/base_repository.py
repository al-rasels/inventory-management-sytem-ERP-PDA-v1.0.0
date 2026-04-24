from abc import ABC, abstractmethod
from typing import List, Any, Optional
import pandas as pd

class BaseRepository(ABC):
    """Abstract base repository for database operations."""
    
    def __init__(self, db):
        self.db = db

    @abstractmethod
    def get_all(self) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_by_id(self, id: Any) -> Optional[dict]:
        pass

    @abstractmethod
    def create(self, data: dict) -> bool:
        pass

    @abstractmethod
    def update(self, id: Any, data: dict) -> bool:
        pass

    @abstractmethod
    def delete(self, id: Any) -> bool:
        pass
