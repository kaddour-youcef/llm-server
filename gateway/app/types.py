"""
Centralized type exports for the Gateway service.

This module aggregates Pydantic models and related data shapes used across the
gateway so other modules can import types from a single place. Keeping imports
cohesive helps maintain type consistency with the admin UI.
"""

from pydantic import BaseModel, Field  # re-export commonly used pydantic names
from typing import Any, List, Optional  # convenience

# Re-export application types from their source modules
from .schemas import (
    ChatMessage,
    ChatCompletionRequest,
    UserCreate,
    UserOut,
    UserUpdate,
    KeyCreate,
    KeyOut,
    UserDetailOut,
    # organizations / teams / memberships
    OrganizationCreate,
    OrganizationOut,
    OrganizationUpdate,
    TeamCreate,
    TeamOut,
    TeamUpdate,
    MembershipCreate,
    MembershipOut,
)
from .auth import Principal
from .config import Settings

__all__ = [
    # pydantic conveniences
    "BaseModel",
    "Field",
    # typing conveniences
    "Any",
    "List",
    "Optional",
    # models from schemas
    "ChatMessage",
    "ChatCompletionRequest",
    "UserCreate",
    "UserOut",
    "UserUpdate",
    "KeyCreate",
    "KeyOut",
    "UserDetailOut",
    # org/team/membership schemas
    "OrganizationCreate",
    "OrganizationOut",
    "OrganizationUpdate",
    "TeamCreate",
    "TeamOut",
    "TeamUpdate",
    "MembershipCreate",
    "MembershipOut",
    # auth principal
    "Principal",
    # settings
    "Settings",
]
