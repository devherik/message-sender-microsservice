
from models.models import Message
from models.interfaces import IDatabaseRepository
from repositories.message_sender_repository import MessageSenderRepository


class MessageService:
    """
    This is our Application/Use Case layer. It orchestrates the domain entities
    and uses repository interfaces to perform tasks. It contains the core
    business logic of the application.
    """

    def __init__(self, db: IDatabaseRepository):
        """
        The service depends on a connection, not the repository itself.
        This makes it more flexible and easier to test.
        """
        self.repository = MessageSenderRepository(db)

    def create_message(self, content: str) -> Message:
        """
        Use Case: Create a new message.
        """
        try:
            # Here we would have more complex business logic, validations, etc.
            message = Message(
                app_id=1,  # In a real scenario, this would come from the context
                sender_phone_number="+1234567890",
                recipient_phone_number="+0987654321",
                message_content=content,
            )

            # Persist the message using the repository
            success = self.repository.persist_message(message)
            if not success:
                raise Exception("Failed to persist message")

            return message
        except Exception as e:
            print(f"Error creating message: {e}")
            raise
