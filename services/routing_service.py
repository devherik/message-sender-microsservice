"""
Application Layer: Routing Service

Implements the Strategy Pattern for data routing.
Applies configurable routing rules to data events.

Why this design?
- Open/Closed Principle: New routing strategies can be added without modifying this class
- Strategy Pattern: Different destination handlers can be plugged in
- Separation of Concerns: Routing logic is separate from ingestion logic
"""

from typing import Dict, Any

from models.data_events import DataEvent, RoutingRule
from models.interfaces import IRoutingRuleRepository, IDataEventRepository
from helpers.logging_helper import logger


class RoutingService:
    """
    Implements the Strategy Pattern for data routing.

    This service:
    1. Fetches active routing rules for an event
    2. Evaluates conditions to find matching rules
    3. Executes matching rules in priority order
    4. Marks the event as processed

    Open/Closed Principle (OCP):
    - Open for extension: New destination types can be added via handlers
    - Closed for modification: Core routing logic remains stable
    """

    def __init__(
        self,
        routing_rule_repository: IRoutingRuleRepository,
        data_event_repository: IDataEventRepository,
    ):
        """
        Constructor injection of dependencies.

        Args:
            routing_rule_repository: Repository for fetching routing rules
            data_event_repository: Repository for marking events as processed
        """
        self.rule_repository = routing_rule_repository
        self.event_repository = data_event_repository

    async def apply_rules(self, event_id: int, event: DataEvent) -> Dict[str, Any]:
        """
        Apply all matching routing rules to the event.

        Business Logic:
        1. Fetch active rules for this app_id and event_type
        2. Evaluate conditions for each rule
        3. Execute matching rules in priority order (highest first)
        4. Mark event as processed
        5. Return execution summary

        Args:
            event_id: The unique identifier of the event
            event: The data event to route

        Returns:
            Dictionary with execution summary
        """
        try:
            # Fetch active rules
            rules = await self.rule_repository.get_active_rules(
                app_id=event.app_id, event_type=event.event_type
            )

            if not rules:
                logger.info(
                    f"No active routing rules found for app_id={event.app_id}, "
                    f"event_type={event.event_type}"
                )
                await self.event_repository.mark_event_processed(event_id)
                return {
                    "event_id": event_id,
                    "rules_evaluated": 0,
                    "rules_matched": 0,
                    "rules_executed": 0,
                }

            # Evaluate and execute rules
            matched_rules = []
            executed_rules = []

            for rule in rules:
                if self._evaluate_condition(rule.condition, event.payload):
                    matched_rules.append(rule.rule_id)

                    # Execute the rule (log for now, can be extended)
                    success = await self._execute_rule(event, rule)
                    if success:
                        executed_rules.append(rule.rule_id)

            # Mark event as processed
            await self.event_repository.mark_event_processed(event_id)

            logger.info(
                f"Routing complete for event {event_id}: "
                f"evaluated={len(rules)}, matched={len(matched_rules)}, "
                f"executed={len(executed_rules)}"
            )

            return {
                "event_id": event_id,
                "rules_evaluated": len(rules),
                "rules_matched": len(matched_rules),
                "rules_executed": len(executed_rules),
                "matched_rule_ids": matched_rules,
                "executed_rule_ids": executed_rules,
            }

        except Exception as e:
            logger.error(f"Error applying routing rules to event {event_id}: {e}")
            return {
                "event_id": event_id,
                "error": str(e),
                "rules_evaluated": 0,
                "rules_matched": 0,
                "rules_executed": 0,
            }

    def _evaluate_condition(
        self, condition: Dict[str, Any], payload: Dict[str, Any]
    ) -> bool:
        """
        Evaluate whether a condition matches the event payload.

        This implements a simple condition evaluation system.
        Supports:
        - Exact match: {"key": "value"}
        - Greater than: {"key": {"$gt": 100}}
        - Less than: {"key": {"$lt": 100}}
        - Exists: {"key": {"$exists": true}}

        Future enhancement: Use a proper JSONPath library for complex queries.

        Args:
            condition: The condition to evaluate
            payload: The event payload to check against

        Returns:
            True if condition matches, False otherwise
        """
        try:
            for key, expected in condition.items():
                # Navigate nested keys (e.g., "payload.user.id")
                value = self._get_nested_value(payload, key)

                # Handle operator-based conditions
                if isinstance(expected, dict):
                    for operator, operand in expected.items():
                        if operator == "$gt":
                            if not (value is not None and value > operand):
                                return False
                        elif operator == "$lt":
                            if not (value is not None and value < operand):
                                return False
                        elif operator == "$gte":
                            if not (value is not None and value >= operand):
                                return False
                        elif operator == "$lte":
                            if not (value is not None and value <= operand):
                                return False
                        elif operator == "$eq":
                            if value != operand:
                                return False
                        elif operator == "$ne":
                            if value == operand:
                                return False
                        elif operator == "$exists":
                            if operand and value is None:
                                return False
                            if not operand and value is not None:
                                return False
                else:
                    # Exact match
                    if value != expected:
                        return False

            return True

        except Exception as e:
            logger.warning(f"Error evaluating condition: {e}")
            return False

    def _get_nested_value(self, data: Dict[str, Any], key_path: str) -> Any:
        """
        Get a value from a nested dictionary using dot notation.

        Example: "user.profile.age" -> data["user"]["profile"]["age"]

        Args:
            data: The dictionary to search
            key_path: Dot-separated path to the value

        Returns:
            The value if found, None otherwise
        """
        keys = key_path.split(".")
        value = data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    async def _execute_rule(self, event: DataEvent, rule: RoutingRule) -> bool:
        """
        Execute a routing rule.

        This is where the actual routing happens. Currently logs the action,
        but can be extended to:
        - Send webhooks
        - Write to different database tables
        - Publish to message queues
        - Trigger external APIs

        Args:
            event: The data event
            rule: The routing rule to execute

        Returns:
            True if execution succeeded, False otherwise
        """
        try:
            destination_type = rule.destination_type
            destination_config = rule.destination_config

            logger.info(
                f"Executing routing rule: rule_id={rule.rule_id}, "
                f"rule_name={rule.rule_name}, destination_type={destination_type}"
            )

            # TODO: Implement actual destination handlers
            # For now, just log the action
            if destination_type == "webhook":
                logger.info(
                    f"Would send webhook to: {destination_config.get('url')} "
                    f"with payload: {event.payload}"
                )
            elif destination_type == "database_table":
                logger.info(
                    f"Would write to table: {destination_config.get('table_name')} "
                    f"with data: {event.payload}"
                )
            elif destination_type == "queue":
                logger.info(
                    f"Would publish to queue: {destination_config.get('queue_name')} "
                    f"with message: {event.payload}"
                )
            else:
                logger.warning(f"Unknown destination type: {destination_type}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error executing routing rule {rule.rule_id}: {e}")
            return False
