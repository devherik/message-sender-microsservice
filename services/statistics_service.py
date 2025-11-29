"""
Application Layer: Statistics Service

Provides analytics and metrics on ingested data.
This service orchestrates statistics queries and aggregations.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from models.data_events import EventStatistics
from models.interfaces import IStatisticsRepository
from helpers.logging_helper import logger


class StatisticsService:
    """
    Application Layer: Provides analytics and metrics.

    Single Responsibility Principle (SRP):
    - This service focuses solely on retrieving and presenting statistics
    - It doesn't handle data ingestion or routing

    Why separate from DataIngestionService?
    - Different concerns: analytics vs. data ingestion
    - Different performance characteristics
    - Allows independent scaling and optimization
    """

    def __init__(self, statistics_repository: IStatisticsRepository):
        """
        Constructor injection of dependencies.

        Args:
            statistics_repository: Repository for statistics queries
        """
        self.repository = statistics_repository

    async def get_event_statistics(
        self,
        app_id: int,
        event_type: Optional[str] = None,
        time_period: str = "daily",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> List[EventStatistics]:
        """
        Retrieve aggregated statistics with flexible filtering.

        Business Logic:
        - Default to last 7 days if no date range specified
        - Validate time_period parameter
        - Return empty list on error (fail gracefully)

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type
            time_period: Granularity ("hourly", "daily", "weekly")
            start_date: Optional start of time range
            end_date: Optional end of time range

        Returns:
            List of EventStatistics objects
        """
        # Validate time_period
        valid_periods = ["hourly", "daily", "weekly"]
        if time_period not in valid_periods:
            logger.error(
                f"Invalid time_period: {time_period}. Must be one of: {valid_periods}"
            )
            raise ValueError(f"time_period must be one of: {valid_periods}")

        # Default date range: last 7 days
        if not start_date:
            start_date = datetime.now() - timedelta(days=7)
        if not end_date:
            end_date = datetime.now()

        try:
            stats = await self.repository.get_aggregated_stats(
                app_id=app_id,
                event_type=event_type,
                time_period=time_period,
                start_date=start_date,
                end_date=end_date,
            )

            logger.info(
                f"Retrieved {len(stats)} statistics for app_id={app_id}, "
                f"time_period={time_period}, event_type={event_type}"
            )

            return stats

        except Exception as e:
            logger.error(f"Error retrieving statistics: {e}")
            return []

    async def get_dashboard_metrics(
        self, app_id: int, time_period: str = "daily"
    ) -> Dict[str, Any]:
        """
        Get pre-computed dashboard metrics for quick visualization.

        This is optimized for dashboard displays where speed is critical.
        Returns a summary across all event types.

        Args:
            app_id: The application identifier
            time_period: Granularity ("hourly", "daily", "weekly")

        Returns:
            Dictionary with aggregated metrics
        """
        # Validate time_period
        valid_periods = ["hourly", "daily", "weekly"]
        if time_period not in valid_periods:
            logger.error(f"Invalid time_period: {time_period}")
            raise ValueError(f"time_period must be one of: {valid_periods}")

        try:
            metrics = await self.repository.get_dashboard_metrics(
                app_id=app_id, time_period=time_period
            )

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

    async def update_statistics_for_period(
        self, app_id: int, event_type: str, time_bucket: datetime, time_period: str
    ) -> bool:
        """
        Trigger an update of pre-aggregated statistics.

        This is typically called by:
        - A background job (e.g., cron job every hour)
        - An async task after event ingestion
        - A manual refresh request

        Args:
            app_id: The application identifier
            event_type: The event type to aggregate
            time_bucket: The time period to aggregate
            time_period: Granularity ("hourly", "daily", "weekly")

        Returns:
            True if successful, False otherwise
        """
        try:
            success = await self.repository.update_statistics(
                app_id=app_id,
                event_type=event_type,
                time_bucket=time_bucket,
                time_period=time_period,
            )

            if success:
                logger.info(
                    f"Updated statistics for app_id={app_id}, "
                    f"event_type={event_type}, time_bucket={time_bucket}"
                )
            else:
                logger.warning(
                    f"Failed to update statistics for app_id={app_id}, "
                    f"event_type={event_type}"
                )

            return success

        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
            return False
