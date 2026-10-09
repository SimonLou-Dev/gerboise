from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ButtonIn(BaseModel):
    label: str
    custom_id: str
    callback_url: str


class EmbedFooter(BaseModel):
    text: str
    icon_url: str | None = None


class EmbedAuthor(BaseModel):
    name: str
    url: str | None = None
    icon_url: str | None = None


class EmbedField(BaseModel):
    name: str
    value: str
    inline: bool = False


class EmbedIn(BaseModel):
    title: str | None = None
    description: str | None = None
    url: str | None = None
    color: int | None = None
    timestamp: datetime | None = None
    footer: EmbedFooter | None = None
    author: EmbedAuthor | None = None
    image_url: str | None = None
    thumbnail_url: str | None = None
    fields: list[EmbedField] = Field(default_factory=list, max_length=25)


class MessageCreate(BaseModel):
    channel_id: str
    content: str
    embed: EmbedIn | None = None
    buttons: list[ButtonIn] = Field(default_factory=list, max_length=5)


class MessagePatch(BaseModel):
    content: str | None = None
    embed: EmbedIn | None = None
    buttons: list[ButtonIn] | None = Field(default=None, max_length=5)


class MessageCreated(BaseModel):
    message_id: str


class ThreadCreate(BaseModel):
    name: str
    auto_archive_duration: Literal[60, 1440, 4320, 10080] = 1440


class ThreadCreated(BaseModel):
    thread_id: str


class ClickUser(BaseModel):
    id: str
    username: str


class ClickPayload(BaseModel):
    message_id: str
    custom_id: str
    user: ClickUser
    clicked_at: datetime
