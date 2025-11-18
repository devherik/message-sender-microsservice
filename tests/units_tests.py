import pytest
from unittest.mock import Mock, AsyncMock
from models.models import MessageRequest
from services.message_service import MessageService
from models.interfaces import IDatabaseRepository


class TestMessageServiceBusinessLogic:
    """
    Unit tests for MessageService.
    
    Why this matters: We test business logic WITHOUT touching the database.
    This is only possible because we followed Dependency Inversion Principle
    and created the IDatabaseRepository abstraction.
    """
    
    @pytest.fixture
    def mock_repository(self):
        """
        Create a mock repository that implements IDatabaseRepository.
        
        This demonstrates the power of interface-based design:
        - No real database needed
        - Tests run instantly
        - Complete control over return values
        """
        mock = Mock(spec=IDatabaseRepository)
        # Configure async methods
        mock.create_message = AsyncMock()
        mock.get_application_by_id = AsyncMock()
        mock.verify_application_credentials = AsyncMock()
        return mock
    
    @pytest.fixture
    def message_service(self, mock_repository):
        """Inject the mock repository into our service."""
        return MessageService(db_repository=mock_repository)
    
    # ============================================================
    # Test 1: Happy Path - Message Creation Success
    # ============================================================
    @pytest.mark.asyncio
    async def test_create_message_success(self, message_service, mock_repository):
        """
        Business Rule: Valid messages should be created and return message_id.
        
        This tests the CORE business logic without any infrastructure concerns.
        """
        # Arrange
        app_id = 123
        request = MessageRequest(
            message_content="Hello, World!",
            phone_number_id=456
        )
        expected_message_id = 789
        
        # Mock the repository to return success
        mock_repository.create_message.return_value = expected_message_id
        
        # Act
        result = await message_service.create_message(app_id, request)
        
        # Assert
        assert result["success"] is True
        assert result["data"]["message_id"] == expected_message_id
        
        # Verify the repository was called with correct parameters
        mock_repository.create_message.assert_called_once()
        call_args = mock_repository.create_message.call_args[0]
        assert call_args[0] == app_id  # app_id
        assert call_args[1] == request.message_content
    
    # ============================================================
    # Test 2: Edge Case - Empty Message Content
    # ============================================================
    @pytest.mark.asyncio
    async def test_create_message_rejects_empty_content(self, message_service, mock_repository):
        """
        Business Rule: Messages must have non-empty content.
        
        Edge case testing is YOUR value-add in the AI era.
        AI rarely thinks of these without explicit guidance.
        """
        # Arrange
        app_id = 123
        request = MessageRequest(
            message_content="",  # Empty content
            phone_number_id=456
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Message content cannot be empty"):
            await message_service.create_message(app_id, request)
        
        # Verify repository was never called (validation failed first)
        mock_repository.create_message.assert_not_called()
    
    # ============================================================
    # Test 3: Edge Case - Extremely Long Message
    # ============================================================
    @pytest.mark.asyncio
    async def test_create_message_rejects_oversized_content(self, message_service, mock_repository):
        """
        Business Rule: Messages should have a maximum length (e.g., 4096 chars).
        
        This is a non-functional requirement that AI won't infer.
        """
        # Arrange
        app_id = 123
        oversized_content = "A" * 5000  # Exceeds limit
        request = MessageRequest(
            message_content=oversized_content,
            phone_number_id=456
        )
        
        # Act & Assert
        with pytest.raises(ValueError, match="Message content exceeds maximum length"):
            await message_service.create_message(app_id, request)
    
    # ============================================================
    # Test 4: Error Handling - Repository Failure
    # ============================================================
    @pytest.mark.asyncio
    async def test_create_message_handles_repository_failure(self, message_service, mock_repository):
        """
        Business Rule: System should handle infrastructure failures gracefully.
        
        This tests your error handling strategy - crucial for production systems.
        """
        # Arrange
        app_id = 123
        request = MessageRequest(
            message_content="Test message",
            phone_number_id=456
        )
        
        # Mock repository to raise an exception
        mock_repository.create_message.side_effect = Exception("Database connection failed")
        
        # Act & Assert
        with pytest.raises(Exception, match="Database connection failed"):
            await message_service.create_message(app_id, request)
    
    # ============================================================
    # Test 5: Behavior Verification - Correlation ID Propagation
    # ============================================================
    @pytest.mark.asyncio
    async def test_create_message_propagates_correlation_id(self, message_service, mock_repository):
        """
        Non-Functional Requirement: Correlation IDs must flow through the system.
        
        This tests observability concerns - critical for distributed systems.
        """
        # Arrange
        app_id = 123
        correlation_id = "test-correlation-123"
        request = MessageRequest(
            message_content="Test",
            phone_number_id=456
        )
        
        mock_repository.create_message.return_value = 789
        
        # Act
        result = await message_service.create_message(
            app_id, 
            request, 
            correlation_id=correlation_id
        )
        
        # Assert - verify correlation_id was logged or passed through
        # (You'd need to add this parameter to your actual service)
        assert "correlation_id" in result["metadata"]
        assert result["metadata"]["correlation_id"] == correlation_id


# ============================================================
# Domain Model Tests
# ============================================================
class TestMessageRequestValidation:
    """
    Test the Pydantic models themselves.
    
    Why: Pydantic handles validation, but you should test YOUR business rules.
    """
    
    def test_message_request_accepts_valid_data(self):
        """Baseline: valid data should pass."""
        request = MessageRequest(
            message_content="Valid message",
            phone_number_id=123
        )
        assert request.message_content == "Valid message"
        assert request.phone_number_id == 123
    
    def test_message_request_rejects_missing_content(self):
        """Business Rule: message_content is required."""
        with pytest.raises(ValueError):
            MessageRequest(phone_number_id=123)
    
    def test_message_request_rejects_invalid_phone_id_type(self):
        """Type Safety: phone_number_id must be integer."""
        with pytest.raises(ValueError):
            MessageRequest(
                message_content="Test",
                phone_number_id="not-an-integer"
            )