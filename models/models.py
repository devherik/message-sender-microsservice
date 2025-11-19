import enum
from datetime import date
from typing import Optional
from pydantic import BaseModel, Field


class LogTypeEnum(str, enum.Enum):
    CREATION = "creation"
    UPDATE = "update"
    DELETION = "deletion"
    ERROR = "error"


class SystemInfo(BaseModel):
    """
    Represents system information.
    args:
        os (str): The operating system of the server.
        python_version (str): The version of Python running the application.
        service_uptime (str): The uptime of the service.
        all_dependencies_working (bool): Indicates if all dependencies are functioning correctly.
        system_tests (dict): A dictionary containing the status of various system tests.
        downtime_start (date): The start date of the last downtime period.
        downtime_end (date): The end date of the last downtime period.
    """

    os: str = Field(..., description="The operating system of the server.")
    python_version: str = Field(
        ..., description="The version of Python running the application."
    )
    service_uptime: str = Field(..., description="The uptime of the service.")
    all_dependencies_working: bool = Field(
        ..., description="Indicates if all dependencies are functioning correctly."
    )
    system_tests: dict = Field(
        default_factory=dict,
        description="A dictionary containing the status of various system tests.",
    )
    downtime_start: date = Field(
        None, description="The start date of the last downtime period."
    )
    downtime_end: date = Field(
        None, description="The end date of the last downtime period."
    )


class Application(BaseModel):
    """
    Represents an application entity within our domain.
    This is a core business object, independent of any framework.
    args:
        app_id (Optional[int]): The unique identifier for the application.
        app_name (str): The name of the application.
        app_key (str): The key of the application.
    """

    app_id: Optional[int] = Field(
        ..., description="The unique identifier for the application."
    )
    app_name: str = Field(..., description="The name of the application.")
    app_key: str = Field(..., description="The key of the application.")


class Message(BaseModel):
    """
    Represents a message entity within our domain.
    This is a core business object, independent of any framework.
    args:
        message_id (Optional[int]): The unique identifier for the message.
        app_id (int): The unique identifier for the message.
        sender_phone_number (str): The sender phone number of the message.
        recipient_phone_number (str): The recipient phone number of the message.
        message_content (str): The text content of the message.
        status (str): The current status of the message.
    """

    message_id: Optional[int] = Field(
        ..., description="The unique identifier for the message."
    )
    app_id: int = Field(..., description="The unique identifier for the message.")
    sender_phone_number_id: int = Field(
        ..., description="The sender phone number ID of the message."
    )
    recipient_phone_number: str = Field(
        ..., description="The recipient phone number of the message."
    )
    message_content: str = Field(..., description="The text content of the message.")
    status: str = Field(
        default="pending", description="The current status of the message."
    )


class MessageLogs(BaseModel):
    """
    Represents a message log entity within our domain.
    This is a core business object, independent of any framework.
    args:
        log_id (Optional[int]): The unique identifier for the message log.
        message_id (int): The unique identifier for the associated message.
        timestamp (str): The timestamp of the log entry.
        status (str): The status recorded in the log entry.
        details (str): Additional details about the log entry.
    """

    log_id: Optional[int] = Field(
        ..., description="The unique identifier for the message log."
    )
    message_id: int = Field(
        ..., description="The unique identifier for the associated message."
    )
    log_message: str = Field(..., description="The log message content.")
    status: LogTypeEnum = Field(
        ..., description="The status recorded in the log entry."
    )


class MessageMetrics(BaseModel):
    """
    Represents message metrics within our domain.
    This is a core business object, independent of any framework.
    args:
        total_messages (int): The total number of messages.
        successful_messages (int): The number of successfully sent messages.
        failed_messages (int): The number of failed messages.
        pending_messages (int): The number of pending messages.
    """

    metric_id: Optional[int] = Field(
        ..., description="The unique identifier for the message metrics."
    )
    message_id: int = Field(
        ..., description="The unique identifier for the associated message."
    )
    sent_at: str = Field(..., description="The timestamp when the message was sent.")
    delivered_at: Optional[str] = Field(
        None, description="The timestamp when the message was delivered."
    )
    failed_at: Optional[str] = Field(
        None, description="The timestamp when the message failed to deliver."
    )
    processing_time_ms: Optional[int] = Field(
        None, description="The processing time in milliseconds."
    )


class PhoneNumber(BaseModel):
    """
    Represents a phone number entity within our domain.
    This is a core business object, independent of any framework.
    args:
        phone_number_id (Optional[int]): The unique identifier for the phone number.
        number (str): The phone number in E.164 format.
        type (str): The type of phone number (e.g., mobile, landline).
        carrier (Optional[str]): The carrier associated with the phone number.
        country_code (str): The country code of the phone number.
    """

    phone_number_id: Optional[int] = Field(
        ..., description="The unique identifier for the phone number."
    )
    phone_number: str = Field(..., description="The phone number in E.164 format.")
    event_type: str = Field(
        ..., description="The type of phone number (e.g., mobile, landline)."
    )
    app_id: int = Field(
        ..., description="The unique identifier for the associated application."
    )
    is_webhook: bool = Field(
        default=False,
        description="Indicates if the phone number is associated with a webhook.",
    )


class Webhook(BaseModel):
    """
    Represents a webhook entity within our domain.
    This is a core business object, independent of any framework.
    args:
        webhook_id (Optional[int]): The unique identifier for the webhook.
        app_id (int): The unique identifier for the associated application.
        url (str): The URL of the webhook.
        event_type (str): The type of event the webhook is associated with.
    """

    webhook_id: Optional[int] = Field(
        ..., description="The unique identifier for the webhook."
    )
    app_id: int = Field(
        ..., description="The unique identifier for the associated application."
    )
    url: str = Field(..., description="The URL of the webhook.")
    event_type: str = Field(
        ..., description="The type of event the webhook is associated with."
    )
