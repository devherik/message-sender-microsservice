"""
Application Layer: Data Ingestion Service

This is the core use case for ingesting data from any source.
This layer contains the business logic and orchestrates domain entities.

Why this layer matters (Clean Architecture):
- Contains the actual business rules
- Independent of frameworks, databases, and UI
- Depends only on domain models and repository interfaces
- Easily testable with mocked dependencies
"""

from typing import Dict, Any, Optional
from datetime import datetime

from models.data_events import DataEvent
from models.interfaces import IDataEventRepository
from helpers.logging_helper import logger


class DataIngestionService:
    """
    Application Layer: Orchestrates the data ingestion workflow.

    Single Responsibility Principle (SRP):
    - This service has ONE job: manage the complete data ingestion lifecycle

    Dependency Inversion Principle (DIP):
    - Depends on IDataEventRepository abstraction, not concrete implementation
    - Can be tested with mocks
    - Can swap database implementations without changing this code

    Business Logic:
    1. Validate incoming data
    2. Enrich with metadata
    3. Persist to database
    4. Return event_id for tracking

    Note: Routing is handled asynchronously by a separate service to keep
    this service focused and fast.
    """

    def __init__(self, data_event_repository: IDataEventRepository):
        """
        Constructor injection of dependencies.

        Args:
            data_event_repository: Repository for persisting data events
        """
        self.repository = data_event_repository

    async def ingest_event(
        self,
        app_id: int,
        event_type: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Core use case: Accept and persist any data event.

        Business Rules:
        1. event_type must be non-empty
        2. payload must be a valid dictionary
        3. metadata is optional but will be enriched with system info
        4. All events start as unprocessed (processed=False)

        Args:
            app_id: The application sending this event
            event_type: Category of event (e.g., "order_created", "user_login")
            payload: The actual event data
            metadata: Optional additional context

        Returns:
            The event_id of the persisted event

        Raises:
            ValueError: If validation fails
            Exception: If persistence fails
        """
        # Business Rule: Validate inputs
        if not event_type or not event_type.strip():
            raise ValueError("event_type cannot be empty")

        if not isinstance(payload, dict):
            raise ValueError("payload must be a dictionary")

        # Enrich metadata with system information
        enriched_metadata = metadata or {}
        enriched_metadata["ingested_at"] = datetime.now().isoformat()

        # Create domain entity
        event = DataEvent(
            event_id=None,  # Will be assigned by database
            app_id=app_id,
            event_type=event_type.strip(),
            payload=payload,
            metadata=enriched_metadata,
            processed=False,
        )

        # Persist using repository
        try:
            event_id = await self.repository.persist_event(event)

            logger.info(
                f"Data ingestion successful: event_id={event_id}, "
                f"app_id={app_id}, event_type={event_type}"
            )

            return event_id

        except Exception as e:
            logger.error(
                f"Data ingestion failed: app_id={app_id}, "
                f"event_type={event_type}, error={str(e)}"
            )
            raise

    async def get_event(self, event_id: int) -> Optional[DataEvent]:
        """
        Retrieve a specific event by ID.

        Args:
            event_id: The unique identifier of the event

        Returns:
            The DataEvent if found, None otherwise
        """
        try:
            event = await self.repository.get_event_by_id(event_id)
            if event:
                logger.info(f"Retrieved event {event_id}")
            else:
                logger.warning(f"Event {event_id} not found")
            return event

        except Exception as e:
            logger.error(f"Error retrieving event {event_id}: {e}")
            return None

    async def get_events_for_app(
        self,
        app_id: int,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DataEvent]:
        """
        Retrieve events for a specific application with pagination.

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            offset: Pagination offset

        Returns:
            List of DataEvent objects
        """
        try:
            events = await self.repository.get_events_by_app(
                app_id=app_id, event_type=event_type, limit=limit, offset=offset
            )

            logger.info(
                f"Retrieved {len(events)} events for app_id={app_id}, "
                f"event_type={event_type}"
            )

            return events

        except Exception as e:
            logger.error(f"Error retrieving events for app {app_id}: {e}")
            return []
