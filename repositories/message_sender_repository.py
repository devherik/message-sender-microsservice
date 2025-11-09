"""
Message Sender Repository
Handles database operations for sending messages
"""


from typing import Any, Dict, Optional
from psycopg2.extensions import connection as PgConnection
from repositories.postgres_repository import PostgresRepository

class MessageSenderRepository:
    def __init__(self, db_repo: PostgresRepository):
        self.db_repo = db_repo

    def send_message(
        self,
        message_content: str
    ) -> bool:
        """
        Sends a message by inserting it into the messages table.
        """
        query = "INSERT INTO messages (content) VALUES (%s);"
        params = {"content": message_content}

        try:
            connection: PgConnection = self.db_repo.get_connection()
            self.db_repo.execute_with_retry(
                query=query,
                params=params,
                connection=connection,
            )
            return True
        except Exception as e:
            print(f"Error sending message: {e}")
            return False
        finally:
            if 'connection' in locals():
                self.db_repo.close_connection(connection)
