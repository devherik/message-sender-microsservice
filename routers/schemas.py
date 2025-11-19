from pydantic import BaseModel, Field


class ResponseModel(BaseModel):
    """
    Represents a generic response model.
    args:
        success (bool): Indicates if the operation was successful.
        message (str): A message providing additional information.
        data (dict): A dictionary containing any relevant data.
    """

    success: bool = Field(..., description="Indicates if the operation was successful.")
    message: str = Field(..., description="A message providing additional information.")
    data: dict = Field(
        default_factory=dict, description="A dictionary containing any relevant data."
    )
