"""
Presentation Layer: Statistics Router

RESTful API endpoints for analytics and metrics.
Provides flexible querying of aggregated statistics.
"""

from typing import Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query

from services.statistics_service import StatisticsService
from routers.schemas import ResponseModel
from helpers.logging_helper import logger


router = APIRouter()


async def get_statistics_service() -> StatisticsService:
    """Dependency injection for StatisticsService."""
    from core.dependencies import get_db_repository
    from repositories.statistics_repository import PostgresStatisticsRepository

    db = get_db_repository()
    stats_repo = PostgresStatisticsRepository(db)
    return StatisticsService(stats_repo)


@router.get("/statistics/{app_id}", response_model=ResponseModel)
async def get_statistics(
    app_id: int,
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    time_period: str = Query("daily", description="Time period: hourly, daily, weekly"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    service: StatisticsService = Depends(get_statistics_service),
):
    """
    Retrieve aggregated statistics with flexible filtering.

    **Query Parameters:**
    - event_type: Optional filter by event type
    - time_period: Granularity (hourly, daily, weekly) - default: daily
    - start_date: Start of time range (ISO format) - default: 7 days ago
    - end_date: End of time range (ISO format) - default: now

    **Example Request:**
    ```
    GET /api/statistics/1?time_period=daily&event_type=order_created
    ```

    **Example Response:**
    ```json
    {
        "success": true,
        "message": "Retrieved 7 statistics",
        "data": {
            "statistics": [
                {
                    "event_type": "order_created",
                    "total_events": 150,
                    "processed_events": 145,
                    "failed_events": 0,
                    "pending_events": 5,
                    "time_bucket": "2025-11-29T00:00:00Z",
                    "time_period": "daily"
                }
            ],
            "count": 7
        }
    }
    ```

    Args:
        app_id: The application identifier
        event_type: Optional filter by event type
        time_period: Granularity
        start_date: Optional start of time range
        end_date: Optional end of time range
        service: Injected statistics service

    Returns:
        ResponseModel with statistics data
    """
    try:
        # Parse dates if provided
        start_dt = None
        end_dt = None

        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use ISO format (e.g., 2025-11-29T00:00:00Z)",
                )

        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use ISO format",
                )

        # Get statistics
        stats = await service.get_event_statistics(
            app_id=app_id,
            event_type=event_type,
            time_period=time_period,
            start_date=start_dt,
            end_date=end_dt,
        )

        return ResponseModel(
            success=True,
            message=f"Retrieved {len(stats)} statistics",
            data={
                "statistics": [stat.model_dump() for stat in stats],
                "count": len(stats),
                "filters": {
                    "app_id": app_id,
                    "event_type": event_type,
                    "time_period": time_period,
                    "start_date": start_date,
                    "end_date": end_date,
                },
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/statistics/dashboard/{app_id}", response_model=ResponseModel)
async def get_dashboard_metrics(
    app_id: int,
    time_period: str = Query("daily", description="Time period: hourly, daily, weekly"),
    service: StatisticsService = Depends(get_statistics_service),
):
    """
    Get pre-computed dashboard metrics for quick visualization.

    Returns a summary across all event types for the application.
    Optimized for dashboard displays where speed is critical.

    **Example Response:**
    ```json
    {
        "success": true,
        "message": "Dashboard metrics retrieved successfully",
        "data": {
            "app_id": 1,
            "time_period": "daily",
            "event_types": [
                {
                    "event_type": "order_created",
                    "total_events": 500,
                    "processed_events": 490,
                    "failed_events": 0,
                    "pending_events": 10
                },
                {
                    "event_type": "user_login",
                    "total_events": 1200,
                    "processed_events": 1200,
                    "failed_events": 0,
                    "pending_events": 0
                }
            ],
            "totals": {
                "total_events": 1700,
                "processed_events": 1690,
                "failed_events": 0,
                "pending_events": 10
            }
        }
    }
    ```

    Args:
        app_id: The application identifier
        time_period: Granularity
        service: Injected statistics service

    Returns:
        ResponseModel with dashboard metrics
    """
    try:
        metrics = await service.get_dashboard_metrics(
            app_id=app_id, time_period=time_period
        )

        return ResponseModel(
            success=True,
            message="Dashboard metrics retrieved successfully",
            data=metrics,
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error retrieving dashboard metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/statistics/refresh/{app_id}", response_model=ResponseModel)
async def refresh_statistics(
    app_id: int,
    event_type: str = Query(..., description="Event type to refresh"),
    time_period: str = Query("daily", description="Time period: hourly, daily, weekly"),
    service: StatisticsService = Depends(get_statistics_service),
):
    """
    Manually trigger a refresh of pre-aggregated statistics.

    This is useful for:
    - On-demand statistics updates
    - Testing statistics aggregation
    - Manual data corrections

    In production, this would typically be called by a background job.

    Args:
        app_id: The application identifier
        event_type: The event type to refresh
        time_period: Granularity
        service: Injected statistics service

    Returns:
        ResponseModel with success status
    """
    try:
        # Calculate time bucket based on period
        now = datetime.now()
        if time_period == "hourly":
            time_bucket = now.replace(minute=0, second=0, microsecond=0)
        elif time_period == "daily":
            time_bucket = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_period == "weekly":
            # Start of week (Monday)
            days_since_monday = now.weekday()
            time_bucket = (now - timedelta(days=days_since_monday)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        else:
            raise ValueError(f"Invalid time_period: {time_period}")

        success = await service.update_statistics_for_period(
            app_id=app_id,
            event_type=event_type,
            time_bucket=time_bucket,
            time_period=time_period,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to refresh statistics",
            )

        return ResponseModel(
            success=True,
            message="Statistics refreshed successfully",
            data={
                "app_id": app_id,
                "event_type": event_type,
                "time_bucket": time_bucket.isoformat(),
                "time_period": time_period,
            },
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error refreshing statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
