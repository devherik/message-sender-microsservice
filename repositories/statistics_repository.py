"""
Infrastructure Layer: Statistics Repository

Concrete implementation of IStatisticsRepository for PostgreSQL.
Handles analytics queries and pre-aggregated statistics.

Why separate repository?
- Single Responsibility Principle (SRP)
- Statistics queries have different performance characteristics
- Allows for specialized optimizations (caching, materialized views)
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from psycopg2.extensions import connection as PgConnection

from models.data_events import EventStatistics
from models.interfaces import IStatisticsRepository
from repositories.database_interfaces import IDatabaseRepository
from helpers.logging_helper import logger


class PostgresStatisticsRepository(IStatisticsRepository):
    """
    PostgreSQL implementation for statistics and analytics.

    This repository provides two approaches:
    1. Pre-aggregated statistics (fast, for dashboards)
    2. On-demand aggregation (flexible, for custom queries)
    """

    def __init__(self, db_repository: IDatabaseRepository):
        self.db = db_repository

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

        Performance strategy:
        - First tries to use pre-aggregated event_statistics table (fast)
        - Falls back to on-demand aggregation if needed (flexible)

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type
            time_period: Granularity ("hourly", "daily", "weekly")
            start_date: Optional start of time range
            end_date: Optional end of time range

        Returns:
            List of EventStatistics objects
        """
        # Try pre-aggregated statistics first
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        if event_type:
            query = """
                SELECT stat_id, app_id, event_type, total_events, 
                       processed_events, failed_events, pending_events,
                       time_bucket, time_period, created_at
                FROM event_statistics
                WHERE app_id = %s 
                  AND event_type = %s
                  AND time_period = %s
                  AND time_bucket BETWEEN %s AND %s
                ORDER BY time_bucket DESC
            """
            params = {
                "app_id": app_id,
                "event_type": event_type,
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date,
            }
        else:
            query = """
                SELECT stat_id, app_id, event_type, total_events, 
                       processed_events, failed_events, pending_events,
                       time_bucket, time_period, created_at
                FROM event_statistics
                WHERE app_id = %s 
                  AND time_period = %s
                  AND time_bucket BETWEEN %s AND %s
                ORDER BY time_bucket DESC, event_type ASC
            """
            params = {
                "app_id": app_id,
                "time_period": time_period,
                "start_date": start_date,
                "end_date": end_date,
            }

        try:
            conn: PgConnection = self.db.get_connection()
            result = self.db.execute_with_retry(query, params, connection=conn)

            stats = []
            if result:
                for row in result:
                    stats.append(
                        EventStatistics(
                            stat_id=row[0],
                            app_id=row[1],
                            event_type=row[2],
                            total_events=row[3],
                            processed_events=row[4],
                            failed_events=row[5],
                            pending_events=row[6],
                            time_bucket=row[7],
                            time_period=row[8],
                            created_at=row[9],
                        )
                    )

            logger.info(
                f"Retrieved {len(stats)} statistics for app_id={app_id}, "
                f"time_period={time_period}"
            )
            return stats

        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            return []

    async def update_statistics(
        self, app_id: int, event_type: str, time_bucket: datetime, time_period: str
    ) -> bool:
        """
        Update pre-aggregated statistics for a specific time bucket.

        This performs an "upsert" (INSERT ... ON CONFLICT UPDATE):
        - If the statistic doesn't exist, create it
        - If it exists, update the counts

        This is typically called by:
        - A background job (e.g., every hour for hourly stats)
        - A database trigger (on data_events INSERT)
        - An async task after event ingestion

        Args:
            app_id: The application identifier
            event_type: The event type to aggregate
            time_bucket: The time period to aggregate
            time_period: Granularity ("hourly", "daily", "weekly")

        Returns:
            True if successful, False otherwise
        """
        query = """
            INSERT INTO event_statistics 
            (app_id, event_type, total_events, processed_events, 
             failed_events, pending_events, time_bucket, time_period, created_at)
            SELECT 
                %s as app_id,
                %s as event_type,
                COUNT(*) as total_events,
                COUNT(CASE WHEN processed = TRUE THEN 1 END) as processed_events,
                0 as failed_events,
                COUNT(CASE WHEN processed = FALSE THEN 1 END) as pending_events,
                %s as time_bucket,
                %s as time_period,
                NOW() as created_at
            FROM data_events
            WHERE app_id = %s
              AND event_type = %s
              AND created_at >= %s
              AND created_at < %s
            ON CONFLICT (app_id, event_type, time_bucket, time_period)
            DO UPDATE SET
                total_events = EXCLUDED.total_events,
                processed_events = EXCLUDED.processed_events,
                pending_events = EXCLUDED.pending_events,
                created_at = NOW()
        """

        # Calculate time range based on period
        if time_period == "hourly":
            time_end = time_bucket + timedelta(hours=1)
        elif time_period == "daily":
            time_end = time_bucket + timedelta(days=1)
        elif time_period == "weekly":
            time_end = time_bucket + timedelta(weeks=1)
        else:
            logger.error(f"Invalid time_period: {time_period}")
            return False

        try:
            conn: PgConnection = self.db.get_connection()
            self.db.execute_with_retry(
                query,
                {
                    "app_id": app_id,
                    "event_type": event_type,
                    "time_bucket": time_bucket,
                    "time_period": time_period,
                    "app_id2": app_id,
                    "event_type2": event_type,
                    "time_start": time_bucket,
                    "time_end": time_end,
                },
                connection=conn,
            )
            logger.info(
                f"Updated statistics for app_id={app_id}, event_type={event_type}, "
                f"time_bucket={time_bucket}, time_period={time_period}"
            )
            return True

        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            return False

    async def get_dashboard_metrics(
        self, app_id: int, time_period: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get pre-computed dashboard metrics for quick visualization.

        Returns a summary across all event types for the application.
        This is optimized for dashboard displays where speed is critical.

        Args:
            app_id: The application identifier
            time_period: Granularity ("hourly", "daily", "weekly")

        Returns:
            Dictionary with aggregated metrics across all event types
        """
        query = """
            SELECT 
                event_type,
                SUM(total_events) as total_events,
                SUM(processed_events) as processed_events,
                SUM(failed_events) as failed_events,
                SUM(pending_events) as pending_events,
                MAX(time_bucket) as latest_bucket
            FROM event_statistics
            WHERE app_id = %s 
              AND time_period = %s
              AND time_bucket >= NOW() - INTERVAL '7 days'
            GROUP BY event_type
            ORDER BY total_events DESC
        """

        try:
            conn: PgConnection = self.db.get_connection()
            result = self.db.execute_with_retry(
                query, {"app_id": app_id, "time_period": time_period}, connection=conn
            )

            metrics = {
                "app_id": app_id,
                "time_period": time_period,
                "event_types": [],
                "totals": {
                    "total_events": 0,
                    "processed_events": 0,
                    "failed_events": 0,
                    "pending_events": 0,
                },
            }

            if result:
                for row in result:
                    event_metrics = {
                        "event_type": row[0],
                        "total_events": row[1],
                        "processed_events": row[2],
                        "failed_events": row[3],
                        "pending_events": row[4],
                        "latest_bucket": row[5].isoformat() if row[5] else None,
                    }
                    metrics["event_types"].append(event_metrics)

                    # Aggregate totals
                    metrics["totals"]["total_events"] += row[1]
                    metrics["totals"]["processed_events"] += row[2]
                    metrics["totals"]["failed_events"] += row[3]
                    metrics["totals"]["pending_events"] += row[4]

            logger.info(f"Retrieved dashboard metrics for app_id={app_id}")
            return metrics

        except Exception as e:
            logger.error(f"Error retrieving dashboard metrics: {e}")
            return {
                "app_id": app_id,
                "time_period": time_period,
                "event_types": [],
                "totals": {
                    "total_events": 0,
                    "processed_events": 0,
                    "failed_events": 0,
                    "pending_events": 0,
                },
                "error": str(e),
            }
