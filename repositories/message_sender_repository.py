"""
Message Sender Repository
Handles database operations for sending messages
"""

from typing import Any, Dict, Optional
from psycopg2.extensions import connection as PgConnection

from models.models import Message, MessageLogs, MessageMetrics
from repositories.postgres_repository import PostgresRepository


class MessageSenderRepository:
    def __init__(self, db_connection: PgConnection):
        self.db_conn = db_connection

    def persist_message(
        self,
        message: Message,
    ) -> bool:
        """
        Sends a message by inserting it into the messages table.
        """
        query = "INSERT INTO messages (app_id, sender_phone_number, recipient_phone_number, message_content, message_type, status) VALUES (%(app_id)s, %(sender_phone_number)s, %(recipient_phone_number)s, %(content)s, 'text', 'pending');"
        params = {
            "app_id": message.app_id,
            "sender_phone_number": message.sender_phone_number,
            "recipient_phone_number": message.recipient_phone_number,
            "content": message.message_content,
        }

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
            if "connection" in locals():
                self.db_repo.close_connection(connection)
