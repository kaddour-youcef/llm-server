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
    # flexible ownership
    owner_type: Optional[str] = None  # 'user' | 'team'; defaults to 'user' if user_id is provided
    owner_id: Optional[str] = None
    # legacy support
    user_id: Optional[str] = None
    # key params
    name: str
    role: Optional[str] = "user"
    monthly_quota_tokens: Optional[int] = None
    daily_request_quota: Optional[int] = None
    expires_at: Optional[str] = None  # ISO datetime or YYYY-MM-DD; null = unlimited


class KeyOut(BaseModel):
    id: str
    owner_type: str
    owner_id: str
    user_id: Optional[str] = None
    name: str
    role: str
    status: str
    last4: str
    expires_at: Optional[str] = None

class UserDetailOut(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    created_at: Optional[str] = None
    status: Optional[str] = None
    keys: list[KeyOut] = []


# Organizations / Teams
class OrganizationCreate(BaseModel):
    name: str
    status: Optional[str] = "active"
    monthly_token_quota: Optional[int] = None


class OrganizationOut(BaseModel):
    id: str
    name: str
    status: Optional[str] = None
    monthly_token_quota: Optional[int] = None


class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    monthly_token_quota: Optional[int] = None


class TeamCreate(BaseModel):
    organization_id: str
    name: str
    description: Optional[str] = None


class TeamOut(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class MembershipCreate(BaseModel):
    team_id: str
    user_id: str
    role: Optional[str] = "member"


class MembershipOut(BaseModel):
    id: str
    team_id: str
    user_id: str
    role: str


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
