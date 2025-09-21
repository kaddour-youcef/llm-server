from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Text, Integer, BigInteger, Date, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import DateTime
from sqlalchemy.sql import func


Base = declarative_base()


class Organization(Base):
    __tablename__ = "organizations"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(Text, nullable=False, unique=True)
    status = Column(Text, nullable=False, server_default="active")
    monthly_token_quota = Column(BigInteger, nullable=True)
    settings = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Team(Base):
    __tablename__ = "teams"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    name = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Membership(Base):
    __tablename__ = "memberships"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    team_id = Column(UUID(as_uuid=True), ForeignKey("teams.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role = Column(Text, nullable=False, server_default="member")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    name = Column(Text, nullable=False)
    email = Column(Text, nullable=True, unique=True)
    # Added for self-service auth
    password_hash = Column(Text, nullable=True)
    status = Column(Text, nullable=False, server_default="pending")  # pending|approved|disabled
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)



class APIKey(Base):
    __tablename__ = "api_keys"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    # Legacy field retained for compatibility when owner_type='user'
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    # Polymorphic ownership
    owner_type = Column(Text, nullable=False)  # 'user' | 'team'
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    name = Column(Text, nullable=False)
    key_hash = Column(Text, nullable=False)
    key_last4 = Column(Text, nullable=False)
    role = Column(Text, nullable=False)
    status = Column(Text, nullable=False)
    monthly_token_quota = Column(BigInteger, nullable=True)
    daily_request_quota = Column(BigInteger, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)



class Request(Base):
    __tablename__ = "requests"
    id = Column(UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()"))
    key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="SET NULL"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True)
    owner_type = Column(Text, nullable=True)  # 'user' | 'team'
    owner_id = Column(UUID(as_uuid=True), nullable=True)
    endpoint = Column(Text, nullable=False)
    model = Column(Text, nullable=True)
    request_body = Column(JSONB, nullable=True)
    response_body = Column(JSONB, nullable=True)
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    prompt_tokens = Column(Integer, nullable=False)
    completion_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    latency_ms = Column(Integer, nullable=True)


class UsageRollup(Base):
    __tablename__ = "usage_rollups"
    id = Column(BigInteger, primary_key=True)
    key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False)
    request_count = Column(BigInteger, nullable=False)
    prompt_tokens = Column(BigInteger, nullable=False)
    completion_tokens = Column(BigInteger, nullable=False)
    total_tokens = Column(BigInteger, nullable=False)


class APIUsage(Base):
    __tablename__ = "api_usage"
    id = Column(BigInteger, primary_key=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    owner_type = Column(Text, nullable=False)
    owner_id = Column(UUID(as_uuid=True), nullable=False)
    key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False)
    day = Column(Date, nullable=False)
    request_count = Column(BigInteger, nullable=False)
    prompt_tokens = Column(BigInteger, nullable=False)
    completion_tokens = Column(BigInteger, nullable=False)
    total_tokens = Column(BigInteger, nullable=False)


class Audit(Base):
    __tablename__ = "audits"
    id = Column(BigInteger, primary_key=True)
    actor_key_id = Column(UUID(as_uuid=True), ForeignKey("api_keys.id"), nullable=True)
    action = Column(Text, nullable=False)
    target_id = Column(UUID(as_uuid=True), nullable=True)
    meta = Column(JSONB, nullable=True)
