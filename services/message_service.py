from models.models import Message, MessageLogs, LogTypeEnum
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
            id = self.repository.persist_message(object)
            if not id:
                raise Exception("Failed to persist message")

            log: MessageLogs = MessageLogs(
                log_id=None,
                message_id=id,
                log_message=message.message_content,
                status=LogTypeEnum.CREATION,
            )
            self.persist_logs(log)
            return True
        except Exception as e:
            print(f"Error creating message: {e}")
            raise

    def persist_logs(self, log: MessageLogs) -> bool:
        """
        Persists a log entry related to a message.
        """
        try:
            object = MessageLogs.model_validate(log)
            return self.repository.log_message_activity(object)
        except Exception as e:
            print(f"Error validating log data: {e}")
            raise
