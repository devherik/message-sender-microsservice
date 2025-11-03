from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IDatabaseService(ABC):
    @abstractmethod
    def get_connection(self) -> Any:
        pass

    @abstractmethod
    def close_connection(self, connection: Any) -> bool:
        pass

    @abstractmethod
    def is_connection_alive(self, connection) -> bool:
        pass

    @abstractmethod
    def execute_with_retry(
        self, query, params: Optional[Dict[str, Any]] = None, max_retries: int = 3
    ) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_connection_info(self) -> Dict[str, Any]:
        pass
