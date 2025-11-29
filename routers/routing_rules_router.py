"""
Presentation Layer: Routing Rules Router

RESTful API endpoints for managing routing rules.
Provides CRUD operations for routing configurations.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from services.routing_rule_service import RoutingRuleService
from models.data_events import RoutingRule
from routers.schemas import ResponseModel
from helpers.logging_helper import logger


router = APIRouter()


class CreateRoutingRuleRequest(BaseModel):
    """Request model for creating a routing rule."""

    app_id: int = Field(..., description="The application identifier")
    rule_name: str = Field(..., description="Human-readable name for the rule")
    event_type_filter: Optional[str] = Field(None, description="Filter by event type")
    condition: dict = Field(..., description="Condition to match events")
    destination_type: str = Field(
        ..., description="Type of destination (webhook, database_table, queue)"
    )
    destination_config: dict = Field(..., description="Destination configuration")
    priority: int = Field(default=0, description="Execution priority")
    is_active: bool = Field(default=True, description="Whether the rule is active")


class UpdateRoutingRuleRequest(BaseModel):
    """Request model for updating a routing rule."""

    rule_name: Optional[str] = Field(
        None, description="Human-readable name for the rule"
    )
    event_type_filter: Optional[str] = Field(None, description="Filter by event type")
    condition: Optional[dict] = Field(None, description="Condition to match events")
    destination_type: Optional[str] = Field(None, description="Type of destination")
    destination_config: Optional[dict] = Field(
        None, description="Destination configuration"
    )
    priority: Optional[int] = Field(None, description="Execution priority")
    is_active: Optional[bool] = Field(None, description="Whether the rule is active")


async def get_routing_rule_service() -> RoutingRuleService:
    """Dependency injection for RoutingRuleService."""
    from core.dependencies import get_db_repository
    from repositories.routing_rule_repository import PostgresRoutingRuleRepository

    db = get_db_repository()
    routing_rule_repo = PostgresRoutingRuleRepository(db)
    return RoutingRuleService(routing_rule_repo)


@router.post(
    "/routing-rules", response_model=ResponseModel, status_code=status.HTTP_201_CREATED
)
async def create_routing_rule(
    request_body: CreateRoutingRuleRequest,
    service: RoutingRuleService = Depends(get_routing_rule_service),
):
    """
    Create a new routing rule.

    **Example Request:**
    ```json
    {
        "app_id": 1,
        "rule_name": "Forward high-value orders",
        "event_type_filter": "order_created",
        "condition": {"payload.total": {"$gt": 50}},
        "destination_type": "webhook",
        "destination_config": {"url": "https://example.com/webhook"},
        "priority": 10
    }
    ```

    Args:
        request_body: The routing rule data
        service: Injected routing rule service

    Returns:
        ResponseModel with rule_id
    """
    try:
        rule = RoutingRule(
            rule_id=None,
            app_id=request_body.app_id,
            rule_name=request_body.rule_name,
            event_type_filter=request_body.event_type_filter,
            condition=request_body.condition,
            destination_type=request_body.destination_type,
            destination_config=request_body.destination_config,
            priority=request_body.priority,
            is_active=request_body.is_active,
        )

        rule_id = await service.create_rule(rule)

        return ResponseModel(
            success=True,
            message="Routing rule created successfully",
            data={"rule_id": rule_id},
        )

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating routing rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/routing-rules/{rule_id}", response_model=ResponseModel)
async def get_routing_rule(
    rule_id: int, service: RoutingRuleService = Depends(get_routing_rule_service)
):
    """
    Retrieve a routing rule by ID.

    Args:
        rule_id: The unique identifier of the rule
        service: Injected routing rule service

    Returns:
        ResponseModel with rule data
    """
    try:
        rule = await service.get_rule(rule_id)

        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Routing rule {rule_id} not found",
            )

        return ResponseModel(
            success=True,
            message="Routing rule retrieved successfully",
            data=rule.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving routing rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/routing-rules/app/{app_id}", response_model=ResponseModel)
async def get_routing_rules_for_app(
    app_id: int,
    event_type: Optional[str] = None,
    service: RoutingRuleService = Depends(get_routing_rule_service),
):
    """
    Retrieve routing rules for an application.

    Query Parameters:
    - event_type: Optional filter by event type

    Args:
        app_id: The application identifier
        event_type: Optional filter by event type
        service: Injected routing rule service

    Returns:
        ResponseModel with list of rules
    """
    try:
        rules = await service.get_rules_for_app(app_id=app_id, event_type=event_type)

        return ResponseModel(
            success=True,
            message=f"Retrieved {len(rules)} routing rules",
            data={"rules": [rule.model_dump() for rule in rules], "count": len(rules)},
        )

    except Exception as e:
        logger.error(f"Error retrieving routing rules for app {app_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.put("/routing-rules/{rule_id}", response_model=ResponseModel)
async def update_routing_rule(
    rule_id: int,
    request_body: UpdateRoutingRuleRequest,
    service: RoutingRuleService = Depends(get_routing_rule_service),
):
    """
    Update an existing routing rule.

    Only provided fields will be updated.

    Args:
        rule_id: The unique identifier of the rule
        request_body: The updated rule data
        service: Injected routing rule service

    Returns:
        ResponseModel with success status
    """
    try:
        # Fetch existing rule
        existing_rule = await service.get_rule(rule_id)
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Routing rule {rule_id} not found",
            )

        # Update only provided fields
        updated_rule = existing_rule.model_copy(
            update={
                k: v for k, v in request_body.model_dump(exclude_unset=True).items()
            }
        )

        success = await service.update_rule(updated_rule)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update routing rule",
            )

        return ResponseModel(
            success=True,
            message="Routing rule updated successfully",
            data={"rule_id": rule_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating routing rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/routing-rules/{rule_id}", response_model=ResponseModel)
async def delete_routing_rule(
    rule_id: int, service: RoutingRuleService = Depends(get_routing_rule_service)
):
    """
    Delete a routing rule.

    Args:
        rule_id: The unique identifier of the rule
        service: Injected routing rule service

    Returns:
        ResponseModel with success status
    """
    try:
        success = await service.delete_rule(rule_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Routing rule {rule_id} not found",
            )

        return ResponseModel(
            success=True,
            message="Routing rule deleted successfully",
            data={"rule_id": rule_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting routing rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.patch("/routing-rules/{rule_id}/toggle", response_model=ResponseModel)
async def toggle_routing_rule(
    rule_id: int,
    is_active: bool,
    service: RoutingRuleService = Depends(get_routing_rule_service),
):
    """
    Enable or disable a routing rule.

    Query Parameters:
    - is_active: True to enable, False to disable

    Args:
        rule_id: The unique identifier of the rule
        is_active: True to enable, False to disable
        service: Injected routing rule service

    Returns:
        ResponseModel with success status
    """
    try:
        success = await service.toggle_rule(rule_id, is_active)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Routing rule {rule_id} not found",
            )

        status_text = "enabled" if is_active else "disabled"

        return ResponseModel(
            success=True,
            message=f"Routing rule {status_text} successfully",
            data={"rule_id": rule_id, "is_active": is_active},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error toggling routing rule {rule_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
