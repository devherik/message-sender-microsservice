from fastapi import APIRouter, Depends
from psycopg2.extensions import connection as PgConnection

from core.dependencies import get_db_connection
from models.models import Message
from services.message_service import MessageService

router = APIRouter()


# This dependency provides the service, which contains our business logic.
def get_message_service(
    db_conn: PgConnection = Depends(get_db_connection),
) -> MessageService:
    """
    Dependency to create a MessageService with a request-scoped database connection.
    """
    return MessageService(db_conn)


@router.post("/messages/", response_model=Message, status_code=201)
def create_message(
    message_content: str, service: MessageService = Depends(get_message_service)
):
    """
    Creates a new message and stores it.

    This endpoint correctly delegates all business logic to the `MessageService`.
    The router's responsibility is only to handle the HTTP request and response.
    """
    return service.create_message(message_content)
