from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from models.models import Message, MessageLogs, MessageMetrics
from models.data_events import DataEvent, RoutingRule, EventStatistics


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


class IDataEventRepository(ABC):
    """
    Abstract interface for data event persistence operations.

    This follows the Dependency Inversion Principle (DIP):
    - High-level modules (services) depend on this abstraction
    - Low-level modules (PostgreSQL implementation) implement this interface
    - Enables easy testing with mocks
    - Allows swapping database implementations
    """

    @abstractmethod
    async def persist_event(self, event: DataEvent) -> int:
        """
        Persist a data event and return its ID.

        Args:
            event: The data event to persist

        Returns:
            The event_id of the persisted event
        """
        pass

    @abstractmethod
    async def get_event_by_id(self, event_id: int) -> Optional[DataEvent]:
        """
        Retrieve a data event by its ID.

        Args:
            event_id: The unique identifier of the event

        Returns:
            The DataEvent if found, None otherwise
        """
        pass

    @abstractmethod
    async def get_events_by_app(
        self,
        app_id: int,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DataEvent]:
        """
        Retrieve data events for a specific application.

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            offset: Pagination offset

        Returns:
            List of DataEvent objects
        """
        pass

    @abstractmethod
    async def mark_event_processed(self, event_id: int) -> bool:
        """
        Mark an event as processed after routing rules have been applied.

        Args:
            event_id: The event to mark as processed

        Returns:
            True if successful, False otherwise
        """
        pass


class IRoutingRuleRepository(ABC):
    """
    Abstract interface for routing rule management.

    This enables the Strategy Pattern:
    - Rules are data-driven, stored in the database
    - New routing strategies can be added without code changes
    """

    @abstractmethod
    async def create_rule(self, rule: RoutingRule) -> int:
        """Create a new routing rule and return its ID."""
        pass

    @abstractmethod
    async def get_rule_by_id(self, rule_id: int) -> Optional[RoutingRule]:
        """Retrieve a routing rule by its ID."""
        pass

    @abstractmethod
    async def get_active_rules(
        self, app_id: int, event_type: Optional[str] = None
    ) -> List[RoutingRule]:
        """
        Retrieve active routing rules for an application.

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type

        Returns:
            List of active RoutingRule objects, sorted by priority (descending)
        """
        pass

    @abstractmethod
    async def update_rule(self, rule: RoutingRule) -> bool:
        """Update an existing routing rule."""
        pass

    @abstractmethod
    async def delete_rule(self, rule_id: int) -> bool:
        """Delete a routing rule."""
        pass

    @abstractmethod
    async def toggle_rule_status(self, rule_id: int, is_active: bool) -> bool:
        """Enable or disable a routing rule."""
        pass


class IStatisticsRepository(ABC):
    """
    Abstract interface for statistics and analytics queries.

    Why separate from IDataEventRepository?
    - Single Responsibility Principle (SRP)
    - Statistics queries have different performance characteristics
    - Allows for specialized optimizations (caching, materialized views, etc.)
    """

    @abstractmethod
    async def get_aggregated_stats(
        self,
        app_id: int,
        event_type: Optional[str] = None,
        time_period: str = "daily",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[EventStatistics]:
        """
        Retrieve aggregated statistics with flexible filtering.

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type
            time_period: Granularity ("hourly", "daily", "weekly")
            start_date: Optional start of time range
            end_date: Optional end of time range

        Returns:
            List of EventStatistics objects
        """
        pass

    @abstractmethod
    async def update_statistics(
        self, app_id: int, event_type: str, time_bucket: datetime, time_period: str
    ) -> bool:
        """
        Update pre-aggregated statistics for a specific time bucket.

        This is typically called by a background job or trigger.

        Args:
            app_id: The application identifier
            event_type: The event type to aggregate
            time_bucket: The time period to aggregate
            time_period: Granularity ("hourly", "daily", "weekly")

        Returns:
            True if successful, False otherwise
        """
        pass

    @abstractmethod
    async def get_dashboard_metrics(
        self, app_id: int, time_period: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get pre-computed dashboard metrics for quick visualization.

        Returns a summary of all event types for the application.

        Args:
            app_id: The application identifier
            time_period: Granularity ("hourly", "daily", "weekly")

        Returns:
            Dictionary with aggregated metrics across all event types
        """
        pass
