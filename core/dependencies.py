from typing import Generator
from psycopg2.extensions import connection as PgConnection

from models.interfaces import IMessageSenderRepository
from repositories.database_interfaces import IDatabaseRepository
from repositories.postgres_repository import PostgresRepository
from repositories.message_sender_repository import MessageSenderRepository

# The repository is instantiated once and shared across the application.
# This is safe because it holds no per-request state.
db_repository = PostgresRepository()


def get_db_connection() -> Generator[PgConnection, None, None]:
    """
    FastAPI dependency to create and clean up a database connection per request.
    """
    connection = None
    try:
        connection = db_repository.get_connection()
        yield connection
    finally:
        if connection:
            db_repository.close_connection(connection)


def get_db_repository() -> IDatabaseRepository:
    """
    FastAPI dependency that provides the database repository.
    This allows us to easily swap the database implementation in the future.
    """
    return db_repository


def get_message_sender_repository(
    db: IDatabaseRepository,
) -> IMessageSenderRepository:
    return MessageSenderRepository(db)
