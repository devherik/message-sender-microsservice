import pytest
import asyncio
from repositories.postgres_repository import PostgresRepository
from core.settings import Settings


@pytest.fixture(scope="session")
def event_loop():
    """
    Create an event loop for the entire test session.
    Required for async tests.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_db_repository():
    """
    Create a real repository connected to a TEST database.

    Critical: Use a separate test database to avoid corrupting production data.
    """
    settings = Settings()
    # Override with test database connection
    settings.DATABASE_URL = "postgresql://test_user:test_pass@localhost:5432/test_db"

    repository = PostgresRepository(settings)

    # Setup: Ensure clean state
    await repository.execute("DELETE FROM messages WHERE message_content LIKE 'TEST_%'")

    yield repository

    # Teardown: Clean up test data
    await repository.execute("DELETE FROM messages WHERE message_content LIKE 'TEST_%'")
    await repository.close()


class TestPostgresRepositoryIntegration:
    """
    Integration tests verify that our repository correctly interacts with PostgreSQL.

    What we're testing:
    - Actual SQL queries work
    - Data is persisted correctly
    - Constraints are enforced
    - Transactions behave correctly
    """

    @pytest.mark.asyncio
    async def test_create_message_persists_to_database(self, test_db_repository):
        """
        Integration Test: Verify message is actually saved to PostgreSQL.
        """
        # Arrange
        app_id = 1
        content = "TEST_integration_message"
        phone_id = 1

        # Act
        message_id = await test_db_repository.create_message(
            app_id=app_id, message_content=content, phone_number_id=phone_id
        )

        # Assert - Query the database to verify persistence
        result = await test_db_repository.execute_fetchone(
            "SELECT * FROM messages WHERE message_id = %s", (message_id,)
        )

        assert result is not None
        assert result["message_content"] == content
        assert result["app_id"] == app_id

    @pytest.mark.asyncio
    async def test_database_enforces_foreign_key_constraints(self, test_db_repository):
        """
        Integration Test: Verify database constraints work correctly.

        This tests that your schema.sql is correct.
        """
        # Arrange - Use a non-existent app_id
        invalid_app_id = 999999

        # Act & Assert - Should raise integrity error
        with pytest.raises(Exception, match="foreign key constraint"):
            await test_db_repository.create_message(
                app_id=invalid_app_id,
                message_content="TEST_invalid_fk",
                phone_number_id=1,
            )

    @pytest.mark.asyncio
    async def test_connection_pool_handles_concurrent_requests(
        self, test_db_repository
    ):
        """
        Integration Test: Verify connection pooling works under load.

        This tests a NON-FUNCTIONAL requirement: concurrency handling.
        """
        # Arrange - Create multiple concurrent write operations
        tasks = [
            test_db_repository.create_message(
                app_id=1, message_content=f"TEST_concurrent_{i}", phone_number_id=1
            )
            for i in range(10)
        ]

        # Act - Execute all concurrently
        message_ids = await asyncio.gather(*tasks)

        # Assert - All messages were created successfully
        assert len(message_ids) == 10
        assert len(set(message_ids)) == 10  # All unique IDs
