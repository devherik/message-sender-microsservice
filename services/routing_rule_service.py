"""
Application Layer: Routing Rule Management Service

Handles CRUD operations for routing rules.
This service provides the business logic for managing routing configurations.
"""

from typing import List, Optional

from models.data_events import RoutingRule
from models.interfaces import IRoutingRuleRepository
from helpers.logging_helper import logger


class RoutingRuleService:
    """
    Application Layer: Manages routing rule lifecycle.

    Single Responsibility Principle (SRP):
    - Focused solely on routing rule management
    - Separate from the actual routing execution (RoutingService)

    This separation allows:
    - Independent testing of rule management vs. rule execution
    - Different scaling strategies
    - Clear separation of concerns
    """

    def __init__(self, routing_rule_repository: IRoutingRuleRepository):
        """
        Constructor injection of dependencies.

        Args:
            routing_rule_repository: Repository for routing rule persistence
        """
        self.repository = routing_rule_repository

    async def create_rule(self, rule: RoutingRule) -> int:
        """
        Create a new routing rule.

        Business Rules:
        - rule_name must be non-empty
        - destination_type must be valid
        - condition must be a valid dictionary

        Args:
            rule: The routing rule to create

        Returns:
            The rule_id of the created rule

        Raises:
            ValueError: If validation fails
        """
        # Validate inputs
        if not rule.rule_name or not rule.rule_name.strip():
            raise ValueError("rule_name cannot be empty")

        valid_destination_types = ["webhook", "database_table", "queue"]
        if rule.destination_type not in valid_destination_types:
            raise ValueError(
                f"destination_type must be one of: {valid_destination_types}"
            )

        if not isinstance(rule.condition, dict):
            raise ValueError("condition must be a dictionary")

        if not isinstance(rule.destination_config, dict):
            raise ValueError("destination_config must be a dictionary")

        try:
            rule_id = await self.repository.create_rule(rule)
            logger.info(
                f"Created routing rule: rule_id={rule_id}, rule_name={rule.rule_name}"
            )
            return rule_id

        except Exception as e:
            logger.error(f"Error creating routing rule: {e}")
            raise

    async def get_rule(self, rule_id: int) -> Optional[RoutingRule]:
        """
        Retrieve a routing rule by ID.

        Args:
            rule_id: The unique identifier of the rule

        Returns:
            The RoutingRule if found, None otherwise
        """
        try:
            rule = await self.repository.get_rule_by_id(rule_id)
            if rule:
                logger.info(f"Retrieved routing rule {rule_id}")
            else:
                logger.warning(f"Routing rule {rule_id} not found")
            return rule

        except Exception as e:
            logger.error(f"Error retrieving routing rule {rule_id}: {e}")
            return None

    async def get_rules_for_app(
        self,
        app_id: int,
        event_type: Optional[str] = None,
        include_inactive: bool = False,
    ) -> List[RoutingRule]:
        """
        Retrieve routing rules for an application.

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type
            include_inactive: Whether to include inactive rules

        Returns:
            List of RoutingRule objects
        """
        try:
            if include_inactive:
                # TODO: Add method to repository to get all rules (active + inactive)
                logger.warning(
                    "include_inactive not yet implemented, returning active only"
                )

            rules = await self.repository.get_active_rules(
                app_id=app_id, event_type=event_type
            )

            logger.info(f"Retrieved {len(rules)} routing rules for app_id={app_id}")
            return rules

        except Exception as e:
            logger.error(f"Error retrieving routing rules for app {app_id}: {e}")
            return []

    async def update_rule(self, rule: RoutingRule) -> bool:
        """
        Update an existing routing rule.

        Args:
            rule: The routing rule with updated values

        Returns:
            True if successful, False otherwise
        """
        if not rule.rule_id:
            raise ValueError("rule_id is required for update")

        try:
            success = await self.repository.update_rule(rule)
            if success:
                logger.info(f"Updated routing rule {rule.rule_id}")
            else:
                logger.warning(f"Failed to update routing rule {rule.rule_id}")
            return success

        except Exception as e:
            logger.error(f"Error updating routing rule {rule.rule_id}: {e}")
            return False

    async def delete_rule(self, rule_id: int) -> bool:
        """
        Delete a routing rule.

        Args:
            rule_id: The unique identifier of the rule to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            success = await self.repository.delete_rule(rule_id)
            if success:
                logger.info(f"Deleted routing rule {rule_id}")
            else:
                logger.warning(f"Failed to delete routing rule {rule_id}")
            return success

        except Exception as e:
            logger.error(f"Error deleting routing rule {rule_id}: {e}")
            return False

    async def toggle_rule(self, rule_id: int, is_active: bool) -> bool:
        """
        Enable or disable a routing rule.

        This is safer than deleting rules - you can temporarily disable
        a rule without losing its configuration.

        Args:
            rule_id: The unique identifier of the rule
            is_active: True to enable, False to disable

        Returns:
            True if successful, False otherwise
        """
        try:
            success = await self.repository.toggle_rule_status(rule_id, is_active)
            if success:
                status = "enabled" if is_active else "disabled"
                logger.info(f"Routing rule {rule_id} {status}")
            else:
                logger.warning(f"Failed to toggle routing rule {rule_id}")
            return success

        except Exception as e:
            logger.error(f"Error toggling routing rule {rule_id}: {e}")
            return False
