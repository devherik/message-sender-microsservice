from psycopg2.extensions import connection as PgConnection

from models.models import Message
from repositories.postgres_repository import PostgresRepository


class MessageService:
    """
    This is our Application/Use Case layer. It orchestrates the domain entities
    and uses repository interfaces to perform tasks. It contains the core
    business logic of the application.
    """

    def __init__(self, db_connection: PgConnection):
        """
        The service depends on a connection, not the repository itself.
        This makes it more flexible and easier to test.
        """
        self.db_repo = PostgresRepository()  # The repository is stateless
        self.connection = db_connection

    def create_message(self, content: str) -> Message:
        """
        Use Case: Create a new message.
        """
        # Here you would define the query to insert a message.
        # For now, we'll simulate it.
        print(f"Creating message with content: {content} in the database.")

        # In a real scenario:
        # query = "INSERT INTO messages (content, status) VALUES (%s, %s) RETURNING id, content, status;"
        # params = (content, 'pending')
        # result = self.db_repo.execute_with_retry(query, params, connection=self.connection)
        # new_id, new_content, new_status = result[0]
        # return Message(id=new_id, content=new_content, status=new_status)

        # For demonstration, we return a mock object.
        return Message(id=1, content=content, status="pending")
