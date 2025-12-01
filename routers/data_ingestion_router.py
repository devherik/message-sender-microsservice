"""
Presentation Layer: Data Ingestion Router

RESTful API endpoints for data ingestion from any source.
This is the entry point for external applications to send data.
"""

from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Request, HTTPException, status, BackgroundTasks
from pydantic import BaseModel, Field


from core.dependencies import get_routing_service
from core.dependencies import get_data_ingestion_service
from services.data_ingestion_service import DataIngestionService
from services.routing_service import RoutingService
from routers.schemas import ResponseModel
from helpers.logging_helper import logger


router = APIRouter()


class IngestEventRequest(BaseModel):
    """
    Request model for data ingestion.

    This is intentionally flexible to accept any type of event data.
    """

    event_type: str = Field(
        ...,
        description="Type of event (e.g., 'order_created', 'user_login')",
        min_length=1,
        max_length=100,
    )
    payload: Dict[str, Any] = Field(
        ..., description="The actual event data as a flexible JSON object"
    )


async def async_apply_routing(
    event_id: int,
    ingestion_service: DataIngestionService,
    routing_service: RoutingService,
):
    """
    Background task to apply routing rules without blocking the HTTP response.

    This function runs AFTER the HTTP response has been sent to the client.
    The client gets immediate confirmation of ingestion, and routing happens
    asynchronously in the background.

    Args:
        event_id: The event to route
        ingestion_service: Service to retrieve the event
        routing_service: Service to apply routing rules
    """
    try:
        event = await ingestion_service.get_event(event_id)
        if event:
            routing_summary = await routing_service.apply_rules(event_id, event)
            logger.info(
                f"Background routing complete for event {event_id}: "
                f"matched={routing_summary.get('rules_matched', 0)}, "
                f"executed={routing_summary.get('rules_executed', 0)}"
            )
        else:
            logger.error(f"Event {event_id} not found for background routing")
    except Exception as e:
        logger.error(f"Error in background routing for event {event_id}: {e}")


@router.post(
    "/ingest/{app_id}",
    response_model=ResponseModel,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_data(
    app_id: int,
    request_body: IngestEventRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    ingestion_service: DataIngestionService = Depends(get_data_ingestion_service),
    routing_service: RoutingService = Depends(get_routing_service),
):
    """
    Universal data ingestion endpoint.

    This endpoint accepts ANY JSON payload from ANY application.
    It's the cornerstone of our versatile data platform.

    **Performance Design:**
    - **Fast Response**: Returns immediately after persisting the event
    - **Background Routing**: Routing rules applied asynchronously
    - **Non-Blocking**: High throughput even with slow routing rules

    **Request Body:**
    ```json
    {
        "event_type": "order_created",
        "payload": {
            "order_id": "ORD-123",
            "customer_id": 456,
            "total": 99.99
        }
    }
    ```

    **Response:**
    ```json
    {
        "success": true,
        "message": "Data ingested successfully",
        "data": {
            "event_id": 789,
            "status": "routing_scheduled"
        }
    }
    ```

    Args:
        app_id: The application identifier
        request_body: The event data
        request: FastAPI request object (for metadata extraction)
        background_tasks: FastAPI background tasks manager
        ingestion_service: Injected data ingestion service
        routing_service: Injected routing service

    Returns:
        ResponseModel with event_id (routing happens in background)
    """
    try:
        # Extract metadata from request
        metadata = {
            "ip_address": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "correlation_id": getattr(request.state, "correlation_id", None),
        }

        # Ingest the event (FAST - just database write)
        event_id = await ingestion_service.ingest_event(
            app_id=app_id,
            event_type=request_body.event_type,
            payload=request_body.payload,
            metadata=metadata,
        )

        # Schedule routing to run in background (NON-BLOCKING)
        # This happens AFTER the HTTP response is sent
        background_tasks.add_task(
            async_apply_routing, event_id, ingestion_service, routing_service
        )

        logger.info(
            f"Data ingestion complete: event_id={event_id}, app_id={app_id}, "
            f"event_type={request_body.event_type}, routing scheduled"
        )

        # Return immediately - client doesn't wait for routing
        return ResponseModel(
            success=True,
            message="Data ingested successfully",
            data={"event_id": event_id, "status": "routing_scheduled"},
        )

    except ValueError as e:
        logger.warning(f"Validation error during ingestion: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error during data ingestion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during data ingestion",
        )


@router.get("/events/{event_id}", response_model=ResponseModel)
async def get_event(
    event_id: int,
    ingestion_service: DataIngestionService = Depends(get_data_ingestion_service),
):
    """
    Retrieve a specific event by ID.

    Args:
        event_id: The unique identifier of the event
        ingestion_service: Injected data ingestion service

    Returns:
        ResponseModel with event data
    """
    try:
        event = await ingestion_service.get_event(event_id)

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Event {event_id} not found",
            )

        return ResponseModel(
            success=True,
            message="Event retrieved successfully",
            data=event.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/events/app/{app_id}", response_model=ResponseModel)
async def get_events_for_app(
    app_id: int,
    event_type: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    ingestion_service: DataIngestionService = Depends(get_data_ingestion_service),
):
    """
    Retrieve events for a specific application with pagination.

    Query Parameters:
    - event_type: Optional filter by event type
    - limit: Maximum number of events to return (default: 100, max: 1000)
    - offset: Pagination offset (default: 0)

    Args:
        app_id: The application identifier
        event_type: Optional filter by event type
        limit: Maximum number of events to return
        offset: Pagination offset
        ingestion_service: Injected data ingestion service

    Returns:
        ResponseModel with list of events
    """
    try:
        # Validate limit
        if limit > 1000:
            limit = 1000

        events = await ingestion_service.get_events_for_app(
            app_id=app_id, event_type=event_type, limit=limit, offset=offset
        )

        return ResponseModel(
            success=True,
            message=f"Retrieved {len(events)} events",
            data={
                "events": [event.model_dump() for event in events],
                "count": len(events),
                "limit": limit,
                "offset": offset,
            },
        )

    except Exception as e:
        logger.error(f"Error retrieving events for app {app_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
