"""
Infrastructure Layer: Data Event Repository

This is the concrete implementation of IDataEventRepository for PostgreSQL.
This layer contains the "details" - database-specific code that the application
layer doesn't need to know about.

Why this separation matters (Clean Architecture):
- Business logic (services) doesn't depend on PostgreSQL
- We can swap databases without changing business logic
- Testing is easier with mocked interfaces
- Infrastructure concerns are isolated
"""

import json
from typing import List, Optional
from datetime import datetime
from psycopg2.extensions import connection as PgConnection

from models.data_events import DataEvent
from models.interfaces import IDataEventRepository
from repositories.database_interfaces import IDatabaseRepository
from helpers.logging_helper import logger


class PostgresDataEventRepository(IDataEventRepository):
    """
    PostgreSQL implementation of data event persistence.

    This implements the Repository Pattern:
    - Abstracts data access logic from business logic
    - Encapsulates SQL queries
    - Provides a clean API for the application layer
    """

    def __init__(self, db_repository: IDatabaseRepository):
        """
        Dependency Injection: We depend on IDatabaseRepository abstraction,
        not on a specific database connection implementation.

        Args:
            db_repository: The database connection manager
        """
        self.db = db_repository

    async def persist_event(self, event: DataEvent) -> int:
        """
        Persist a data event to PostgreSQL.

        Why JSONB?
        - Flexible schema for arbitrary event payloads
        - Efficient indexing with GIN indexes
        - Native PostgreSQL support for JSON queries

        Args:
            event: The data event to persist

        Returns:
            The event_id of the persisted event
        """
        query = """
            INSERT INTO data_events 
            (app_id, event_type, payload, metadata, processed, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
            RETURNING event_id
        """

        try:
            conn: PgConnection = self.db.get_connection()

            result = self.db.execute_with_retry(
                query,
                {
                    "app_id": event.app_id,
                    "event_type": event.event_type,
                    "payload": json.dumps(event.payload),
                    "metadata": json.dumps(event.metadata),
                    "processed": event.processed,
                },
                connection=conn,
            )

            if result and len(result) > 0:
                event_id = result[0][0]
                logger.info(
                    f"Persisted data event: event_id={event_id}, "
                    f"app_id={event.app_id}, event_type={event.event_type}"
                )
                return event_id
            else:
                raise Exception("Failed to persist data event: no event_id returned")

        except Exception as e:
            logger.error(f"Error persisting data event: {e}")
            raise

    async def get_event_by_id(self, event_id: int) -> Optional[DataEvent]:
        """
        Retrieve a data event by its ID.

        Args:
            event_id: The unique identifier of the event

        Returns:
            The DataEvent if found, None otherwise
        """
        query = """
            SELECT event_id, app_id, event_type, payload, metadata, 
                   processed, created_at
            FROM data_events
            WHERE event_id = %s
        """

        try:
            conn: PgConnection = self.db.get_connection()
            result = self.db.execute_with_retry(
                query, {"event_id": event_id}, connection=conn
            )

            if result and len(result) > 0:
                row = result[0]
                return DataEvent(
                    event_id=row[0],
                    app_id=row[1],
                    event_type=row[2],
                    payload=json.loads(row[3]) if isinstance(row[3], str) else row[3],
                    metadata=json.loads(row[4]) if isinstance(row[4], str) else row[4],
                    processed=row[5],
                    created_at=row[6],
                )
            return None

        except Exception as e:
            logger.error(f"Error retrieving event {event_id}: {e}")
            return None

    async def get_events_by_app(
        self,
        app_id: int,
        event_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DataEvent]:
        """
        Retrieve data events for a specific application with pagination.

        Performance consideration:
        - Uses indexed columns (app_id, event_type, created_at)
        - LIMIT/OFFSET for pagination
        - Ordered by created_at DESC for most recent first

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type
            limit: Maximum number of events to return
            offset: Pagination offset

        Returns:
            List of DataEvent objects
        """
        if event_type:
            query = """
                SELECT event_id, app_id, event_type, payload, metadata, 
                       processed, created_at
                FROM data_events
                WHERE app_id = %s AND event_type = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = {
                "app_id": app_id,
                "event_type": event_type,
                "limit": limit,
                "offset": offset,
            }
        else:
            query = """
                SELECT event_id, app_id, event_type, payload, metadata, 
                       processed, created_at
                FROM data_events
                WHERE app_id = %s
                ORDER BY created_at DESC
                LIMIT %s OFFSET %s
            """
            params = {"app_id": app_id, "limit": limit, "offset": offset}

        try:
            conn: PgConnection = self.db.get_connection()
            result = self.db.execute_with_retry(query, params, connection=conn)

            events = []
            if result:
                for row in result:
                    events.append(
                        DataEvent(
                            event_id=row[0],
                            app_id=row[1],
                            event_type=row[2],
                            payload=json.loads(row[3])
                            if isinstance(row[3], str)
                            else row[3],
                            metadata=json.loads(row[4])
                            if isinstance(row[4], str)
                            else row[4],
                            processed=row[5],
                            created_at=row[6],
                        )
                    )

            logger.info(f"Retrieved {len(events)} events for app_id={app_id}")
            return events

        except Exception as e:
            logger.error(f"Error retrieving events for app {app_id}: {e}")
            return []

    async def mark_event_processed(self, event_id: int) -> bool:
        """
        Mark an event as processed after routing rules have been applied.

        This is important for:
        - Avoiding duplicate processing
        - Tracking which events have been handled
        - Monitoring system health

        Args:
            event_id: The event to mark as processed

        Returns:
            True if successful, False otherwise
        """
        query = """
            UPDATE data_events
            SET processed = TRUE
            WHERE event_id = %s
        """

        try:
            conn: PgConnection = self.db.get_connection()
            self.db.execute_with_retry(query, {"event_id": event_id}, connection=conn)
            logger.info(f"Marked event {event_id} as processed")
            return True

        except Exception as e:
            logger.error(f"Error marking event {event_id} as processed: {e}")
            return False
