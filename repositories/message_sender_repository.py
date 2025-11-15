"""
Message Sender Repository
Handles database operations for sending messages
"""

from psycopg2.extensions import connection as PgConnection

from models.interfaces import IDatabaseRepository
from models.models import Message, MessageLogs, MessageMetrics


class MessageSenderRepository:
    def __init__(self, db: IDatabaseRepository):
        self.db_repo = db

    def persist_message(
        self,
        message: Message,
    ) -> bool:
        """
        Sends a message by inserting it into the messages table.
        """
        query = "INSERT INTO messages (app_id, sender_id, recipient_phone_number, message_content, message_type, status) VALUES (%(app_id)s, %(sender_phone_number_id)s, %(recipient_phone_number)s, %(content)s, 'text', 'pending');"
        params = {
            "app_id": message.app_id,
            "sender_phone_number_id": message.sender_phone_number_id,
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

    def log_message_activity(
        self,
        log: MessageLogs,
    ) -> bool:
        """
        Logs message activity into the message_logs table.
        """
        query = "INSERT INTO message_logs (message_id, log_type, log_content) VALUES (%(message_id)s, %(log_type)s, %(log_content)s);"
        params = {
            "message_id": log.message_id,
            "log_type": log.log_type,
            "log_content": log.log_content,
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
            print(f"Error logging message activity: {e}")
            return False
        finally:
            if "connection" in locals():
                self.db_repo.close_connection(connection)

    def record_message_metrics(
        self,
        metrics: MessageMetrics,
    ) -> bool:
        """
        Records message metrics into the message_metrics table.
        """
        query = "INSERT INTO message_metrics (message_id, delivery_time_ms, status) VALUES (%(message_id)s, %(delivery_time_ms)s, %(status)s);"
        params = {
            "message_id": metrics.message_id,
            "delivery_time_ms": metrics.delivery_time_ms,
            "status": metrics.status,
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
            print(f"Error recording message metrics: {e}")
            return False
        finally:
            if "connection" in locals():
                self.db_repo.close_connection(connection)
