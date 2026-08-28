from typing import List, Dict, Optional
from abc import ABC, abstractmethod

class BaseConnector(ABC):
    @abstractmethod
    def fetch_feed(self, target: str) -> List[Dict]:
        pass

    @abstractmethod
    def fetch_account(self, target: str, limit: int = 15) -> List[Dict]:
        pass
