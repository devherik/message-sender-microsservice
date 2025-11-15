
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

    def create_message(self, message: Message) -> bool:
        """
        Use Case: Create a new message.
        """
        try:
            object = Message.model_validate(message)

            # Persist the message using the repository
            success = self.repository.persist_message(object)
            if not success:
                raise Exception("Failed to persist message")

            return success
        except Exception as e:
            print(f"Error creating message: {e}")
            raise
