from datetime import date
from pydantic import BaseModel, Field


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


class Message(BaseModel):
    """
    Represents a message entity within our domain.
    This is a core business object, independent of any framework.
    """

    id: int = Field(..., description="The unique identifier for the message.")
    content: str = Field(..., description="The text content of the message.")
    status: str = Field(
        default="pending", description="The current status of the message."
    )


class ResponseModel(BaseModel):
    """
    Represents a generic response model.
    """

    success: bool = Field(..., description="Indicates if the operation was successful.")
    message: str = Field(..., description="A message providing additional information.")
    data: dict = Field(
        default_factory=dict, description="A dictionary containing any relevant data."
    )
