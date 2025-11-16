from fastapi import APIRouter, Depends

from core.dependencies import get_db_service
from models.interfaces import IDatabaseRepository
from models.models import Message, ResponseModel
from services.message_service import MessageService

router = APIRouter()


# This dependency provides the service, which contains our business logic.
def get_message_service(
    db: IDatabaseRepository = Depends(get_db_service),
) -> MessageService:
    """
    Dependency to create a MessageService with a request-scoped database connection.
    """
    return MessageService(db)


@router.post("/messages/{app_id}", response_model=ResponseModel, status_code=201)
def create_message(
    app_id: int,
    message_content: str,
    service: MessageService = Depends(get_message_service),
):
    """
    Creates a new message and stores it.

    This endpoint correctly delegates all business logic to the `MessageService`.
    The router's responsibility is only to handle the HTTP request and response.
    """
    if not message_content:
        return ResponseModel(
            success=False,
            message="Message content cannot be empty",
            data={},
        )
    if not app_id or app_id <= 0:
        return ResponseModel(
            success=False,
            message="Invalid application ID",
            data={},
        )
    message = Message(
        message_id=None,
        app_id=app_id,
        sender_phone_number_id=1,
        recipient_phone_number="+0987654321",
        message_content=message_content,
        status="pending",
    )
    id = service.create_message(message)
    success = id is not None
    return ResponseModel(
        success=success,
        message="Message created successfully"
        if success
        else "Failed to create message",
        data={"message_id": id} if success else {},
    )
