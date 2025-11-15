from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from psycopg2.extensions import connection as PgConnection


class IDatabaseRepository(ABC):
    @abstractmethod
    def get_connection(self) -> PgConnection:
        pass

    @abstractmethod
    def close_connection(self, connection: PgConnection) -> None:
        pass

    @abstractmethod
    def is_connection_alive(self, connection: PgConnection) -> bool:
        pass

    @abstractmethod
    def execute_with_retry(
        self,
        query: str,
        params: Optional[Dict[str, Any]],
        max_retries: int,
        connection: PgConnection,
    ) -> Any:
        pass

    @abstractmethod
    def get_connection_info(self, connection: PgConnection) -> Dict[str, Any]:
        pass
