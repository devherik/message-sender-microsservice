from abc import ABC, abstractmethod

from models.models import Message, MessageLogs, MessageMetrics


class IMessageSenderRepository(ABC):
    @abstractmethod
    def persist_message(
        self,
        message: Message,
    ) -> int | None:
        pass

    @abstractmethod
    def log_message_activity(
        self,
        log: MessageLogs,
    ) -> bool:
        pass

    @abstractmethod
    def record_message_metrics(
        self,
        metrics: MessageMetrics,
    ) -> bool:
        pass
