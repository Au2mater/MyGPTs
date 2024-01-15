from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import Literal
from datetime import datetime
from uuid import uuid4


class GlobalSetting(BaseModel, validate_assignment=True):
    """data class for a global setting"""

    id: str
    value: str
    default_value: str
    type: Literal["str", "int", "bool", "float"] = "str"
    last_updated: datetime = Field(default_factory=datetime.now)
    # set id field to same string as name value

    @field_validator(
        "id", "value", "default_value", "type", "last_updated", mode="before"
    )
    def to_string(cls, v):
        if isinstance(v, type):
            return v.__name__
        return str(v)


# a user class with user id, creation_datime
class User(BaseModel, validate_assignment=True):
    """data class for a user"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    creation_datetime: datetime = Field(default_factory=datetime.now)
    username: str = ""
    email: EmailStr = ""
    password: str = ""


class LLM(BaseModel, validate_assignment=True):
    """LLM model deployment data class"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    api_type: Literal["azure", "openai", "localhost"]
    deployment: str = ""
    enpoint_or_base_url: str
    api_key: str = "not-needed"
    description: str = ""
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


# input to source
class Source(BaseModel, validate_assignment=True):
    """data class for a knowledge sources"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    name: str = Field(min_length=1, max_length=1000)
    source_type: Literal["url", "file path", "uploaded file"]
    creation_time: datetime = Field(default_factory=datetime.now)
    content_type: Literal["txt", "pdf", "csv", "docx", "doc", "md", "url"] = "txt"
    content: str = Field(min_length=1, max_length=500000)
    collection_name_and_assistant_id: str = Field(min_length=1, max_length=100)


# each assistant has one owner indicated in the owner_id field
# create an assistant data class that correponds to a row in the assistants table
class Assistant(BaseModel):
    """data class for an assistant"""

    id: str = Field(default_factory=lambda: uuid4().hex)
    # id is also the name of the assistant's collection in chroma
    name: str = Field(min_length=1, max_length=30)
    # must correspond to one of the deployed models in the llms table
    # this ensures that each assistant has a one unique collection
    chat_model_name: str = Field(min_length=1)
    system_prompt: str = Field(min_length=15)
    temperature: float = Field(ge=0.0, le=2.0, default=0.7)
    welcome_message: str = Field(min_length=3)
    creation_time: datetime = datetime.now()
    last_updated: datetime = datetime.now()
    owner_id: str = Field(min_length=1, max_length=30)
    is_active: bool = True
