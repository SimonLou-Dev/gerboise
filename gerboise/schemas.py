from datetime import datetime

from pydantic import BaseModel, Field


class ButtonIn(BaseModel):
    label: str
    custom_id: str
    callback_url: str


class MessageCreate(BaseModel):
    channel_id: str
    content: str
    buttons: list[ButtonIn] = Field(default_factory=list, max_length=5)


class MessagePatch(BaseModel):
    content: str | None = None
    buttons: list[ButtonIn] | None = Field(default=None, max_length=5)


class MessageCreated(BaseModel):
    message_id: str


class ClickUser(BaseModel):
    id: str
    username: str


class ClickPayload(BaseModel):
    message_id: str
    custom_id: str
    user: ClickUser
    clicked_at: datetime
