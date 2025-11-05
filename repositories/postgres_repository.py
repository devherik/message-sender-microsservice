import psycopg2
from psycopg2.extensions import connection as PgConnection
from typing import Any, Dict, Optional

from core.settings import settings
from models.interfaces import IDatabaseService


class PostgresRepository(IDatabaseService):
    def __init__(self):
        self.dsn = settings.get_postgres_dsn
        if not self.dsn:
            raise ValueError("Postgres DSN is not configured properly.")

    def get_connection(self) -> PgConnection:
        """Establishes and returns a new database connection."""
        try:
            return psycopg2.connect(self.dsn)
        except psycopg2.OperationalError as e:
            # It's better to log this error and re-raise or handle it upstream
            # For now, we'll print and raise a more generic exception
            print(f"Fatal: Could not connect to the database: {e}")
            raise ConnectionError("Failed to connect to the database.") from e

    def close_connection(self, connection: PgConnection) -> None:
        """Closes the given database connection."""
        if connection and not connection.closed:
            connection.close()

    def is_connection_alive(self, connection: PgConnection) -> bool:
        """Checks if the connection is alive and usable."""
        return connection is not None and connection.closed == 0

    def execute_with_retry(
        self,
        query: str,
        params: Optional[Dict[str, Any]] = None,
        max_retries: int = 3,
        connection: Optional[PgConnection] = None,
    ) -> Any:
        """
        Executes a query with retry logic on a given connection.
        The connection is managed by the caller (e.g., a FastAPI dependency).
        """
        if not connection or connection.closed:
            raise ConnectionError(
                "A valid database connection must be provided."
            )

        last_exception = None
        for attempt in range(max_retries):
            try:
                with connection.cursor() as cursor:
                    cursor.execute(query, params)
                    connection.commit()
                    # fetchall() might not be what you always want.
                    # Consider returning the cursor to let the caller decide.
                    if cursor.description:
                        return cursor.fetchall()
                    return None  # For INSERT/UPDATE/DELETE with no returning clause
            except (
                psycopg2.OperationalError,
                psycopg2.DatabaseError,
                psycopg2.IntegrityError,
            ) as e:
                print(f"Database error on attempt {attempt + 1}: {e}")
                last_exception = e
                connection.rollback()  # Rollback on error
                if attempt == max_retries - 1:
                    raise e  # Re-raise the last exception after all retries fail
        raise last_exception

    def get_connection_info(self, connection: PgConnection) -> Dict[str, Any]:
        """Gets information about the given database connection."""
        if not connection:
            return {"dsn": self.dsn, "status": "disconnected"}

        return {
            "dsn": self.dsn,
            "status": "connected"
            if self.is_connection_alive(connection)
            else "disconnected",
        }
