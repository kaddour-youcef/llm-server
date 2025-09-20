from pydantic import BaseModel, Field
from typing import List, Optional, Any


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[ChatMessage]
    stream: Optional[bool] = Field(default=False)
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    presence_penalty: Optional[float] = None
    frequency_penalty: Optional[float] = None
    stop: Optional[Any] = None


# Admin / Users
class UserCreate(BaseModel):
    name: str
    email: Optional[str] = None


class UserOut(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    status: Optional[str] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    status: Optional[str] = None


class KeyCreate(BaseModel):
    user_id: str
    name: str
    role: Optional[str] = "user"
    monthly_quota_tokens: Optional[int] = None
    daily_request_quota: Optional[int] = None


class KeyOut(BaseModel):
    id: str
    user_id: str
    name: str
    role: str
    status: str
    last4: str

class UserDetailOut(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    created_at: Optional[str] = None
    status: Optional[str] = None
    keys: list[KeyOut] = []


# Public auth flows
class SelfRegister(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
