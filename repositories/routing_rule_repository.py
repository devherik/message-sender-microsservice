"""
Infrastructure Layer: Routing Rule Repository

Concrete implementation of IRoutingRuleRepository for PostgreSQL.
Manages the persistence and retrieval of routing rules.
"""

import json
from typing import List, Optional
from psycopg2.extensions import connection as PgConnection

from models.data_events import RoutingRule
from models.interfaces import IRoutingRuleRepository
from repositories.database_interfaces import IDatabaseRepository
from helpers.logging_helper import logger


class PostgresRoutingRuleRepository(IRoutingRuleRepository):
    """
    PostgreSQL implementation of routing rule management.

    This repository handles CRUD operations for routing rules,
    which define how data should be redirected based on conditions.
    """

    def __init__(self, db_repository: IDatabaseRepository):
        self.db = db_repository

    async def create_rule(self, rule: RoutingRule) -> int:
        """
        Create a new routing rule.

        Args:
            rule: The routing rule to create

        Returns:
            The rule_id of the created rule
        """
        query = """
            INSERT INTO routing_rules 
            (app_id, rule_name, event_type_filter, condition, destination_type, 
             destination_config, priority, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
            RETURNING rule_id
        """

        try:
            conn: PgConnection = self.db.get_connection()

            result = self.db.execute_with_retry(
                query,
                {
                    "app_id": rule.app_id,
                    "rule_name": rule.rule_name,
                    "event_type_filter": rule.event_type_filter,
                    "condition": json.dumps(rule.condition),
                    "destination_type": rule.destination_type,
                    "destination_config": json.dumps(rule.destination_config),
                    "priority": rule.priority,
                    "is_active": rule.is_active,
                },
                connection=conn,
            )

            if result and len(result) > 0:
                rule_id = result[0][0]
                logger.info(
                    f"Created routing rule: rule_id={rule_id}, "
                    f"rule_name={rule.rule_name}, app_id={rule.app_id}"
                )
                return rule_id
            else:
                raise Exception("Failed to create routing rule: no rule_id returned")

        except Exception as e:
            logger.error(f"Error creating routing rule: {e}")
            raise

    async def get_rule_by_id(self, rule_id: int) -> Optional[RoutingRule]:
        """Retrieve a routing rule by its ID."""
        query = """
            SELECT rule_id, app_id, rule_name, event_type_filter, condition,
                   destination_type, destination_config, priority, is_active,
                   created_at, updated_at
            FROM routing_rules
            WHERE rule_id = %s
        """

        try:
            conn: PgConnection = self.db.get_connection()
            result = self.db.execute_with_retry(
                query, {"rule_id": rule_id}, connection=conn
            )

            if result and len(result) > 0:
                row = result[0]
                return RoutingRule(
                    rule_id=row[0],
                    app_id=row[1],
                    rule_name=row[2],
                    event_type_filter=row[3],
                    condition=json.loads(row[4]) if isinstance(row[4], str) else row[4],
                    destination_type=row[5],
                    destination_config=json.loads(row[6])
                    if isinstance(row[6], str)
                    else row[6],
                    priority=row[7],
                    is_active=row[8],
                    created_at=row[9],
                    updated_at=row[10],
                )
            return None

        except Exception as e:
            logger.error(f"Error retrieving routing rule {rule_id}: {e}")
            return None

    async def get_active_rules(
        self, app_id: int, event_type: Optional[str] = None
    ) -> List[RoutingRule]:
        """
        Retrieve active routing rules for an application.

        Critical for routing logic:
        - Only returns active rules (is_active = TRUE)
        - Filters by event_type if provided
        - Orders by priority DESC (higher priority first)

        Args:
            app_id: The application identifier
            event_type: Optional filter by event type

        Returns:
            List of active RoutingRule objects, sorted by priority
        """
        if event_type:
            query = """
                SELECT rule_id, app_id, rule_name, event_type_filter, condition,
                       destination_type, destination_config, priority, is_active,
                       created_at, updated_at
                FROM routing_rules
                WHERE app_id = %s 
                  AND is_active = TRUE
                  AND (event_type_filter IS NULL OR event_type_filter = %s)
                ORDER BY priority DESC, rule_id ASC
            """
            params = {"app_id": app_id, "event_type": event_type}
        else:
            query = """
                SELECT rule_id, app_id, rule_name, event_type_filter, condition,
                       destination_type, destination_config, priority, is_active,
                       created_at, updated_at
                FROM routing_rules
                WHERE app_id = %s AND is_active = TRUE
                ORDER BY priority DESC, rule_id ASC
            """
            params = {"app_id": app_id}

        try:
            conn: PgConnection = self.db.get_connection()
            result = self.db.execute_with_retry(query, params, connection=conn)

            rules = []
            if result:
                for row in result:
                    rules.append(
                        RoutingRule(
                            rule_id=row[0],
                            app_id=row[1],
                            rule_name=row[2],
                            event_type_filter=row[3],
                            condition=json.loads(row[4])
                            if isinstance(row[4], str)
                            else row[4],
                            destination_type=row[5],
                            destination_config=json.loads(row[6])
                            if isinstance(row[6], str)
                            else row[6],
                            priority=row[7],
                            is_active=row[8],
                            created_at=row[9],
                            updated_at=row[10],
                        )
                    )

            logger.info(
                f"Retrieved {len(rules)} active routing rules for app_id={app_id}"
            )
            return rules

        except Exception as e:
            logger.error(f"Error retrieving routing rules for app {app_id}: {e}")
            return []

    async def update_rule(self, rule: RoutingRule) -> bool:
        """Update an existing routing rule."""
        query = """
            UPDATE routing_rules
            SET rule_name = %s,
                event_type_filter = %s,
                condition = %s,
                destination_type = %s,
                destination_config = %s,
                priority = %s,
                is_active = %s,
                updated_at = NOW()
            WHERE rule_id = %s
        """

        try:
            conn: PgConnection = self.db.get_connection()
            self.db.execute_with_retry(
                query,
                {
                    "rule_name": rule.rule_name,
                    "event_type_filter": rule.event_type_filter,
                    "condition": json.dumps(rule.condition),
                    "destination_type": rule.destination_type,
                    "destination_config": json.dumps(rule.destination_config),
                    "priority": rule.priority,
                    "is_active": rule.is_active,
                    "rule_id": rule.rule_id,
                },
                connection=conn,
            )
            logger.info(f"Updated routing rule {rule.rule_id}")
            return True

        except Exception as e:
            logger.error(f"Error updating routing rule {rule.rule_id}: {e}")
            return False

    async def delete_rule(self, rule_id: int) -> bool:
        """Delete a routing rule."""
        query = "DELETE FROM routing_rules WHERE rule_id = %s"

        try:
            conn: PgConnection = self.db.get_connection()
            self.db.execute_with_retry(query, {"rule_id": rule_id}, connection=conn)
            logger.info(f"Deleted routing rule {rule_id}")
            return True

        except Exception as e:
            logger.error(f"Error deleting routing rule {rule_id}: {e}")
            return False

    async def toggle_rule_status(self, rule_id: int, is_active: bool) -> bool:
        """Enable or disable a routing rule."""
        query = """
            UPDATE routing_rules
            SET is_active = %s, updated_at = NOW()
            WHERE rule_id = %s
        """

        try:
            conn: PgConnection = self.db.get_connection()
            self.db.execute_with_retry(
                query, {"is_active": is_active, "rule_id": rule_id}, connection=conn
            )
            status = "enabled" if is_active else "disabled"
            logger.info(f"Routing rule {rule_id} {status}")
            return True

        except Exception as e:
            logger.error(f"Error toggling routing rule {rule_id}: {e}")
            return False
