from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_polymorphic_keys"
down_revision = "0003_add_expires_at_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1) Organizations
    op.create_table(
        "organizations",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.Text(), nullable=False, unique=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="active"),
        sa.Column("monthly_token_quota", sa.BigInteger(), nullable=True),
        sa.Column("settings", sa.dialects.postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # Create a default organization and attach all existing users to it
    op.execute("""
        INSERT INTO organizations (id, name, status)
        VALUES (gen_random_uuid(), 'Default Organization', 'active')
    """)

    # 2) Teams
    op.create_table(
        "teams",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("organization_id", "name", name="uq_teams_org_name"),
    )

    # 3) Memberships
    op.create_table(
        "memberships",
        sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("team_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("teams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default="member"),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("team_id", "user_id", name="uq_memberships_team_user"),
    )

    # 4) Users: add organization_id (many users → one org)
    op.add_column(
        "users",
        sa.Column("organization_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True),
    )
    # Set all existing users to the single default org created above
    op.execute(
        """
        UPDATE users SET organization_id = (
            SELECT id FROM organizations WHERE name = 'Default Organization' LIMIT 1
        )
        """
    )
    # Now enforce NOT NULL + FK
    op.alter_column(
        "users",
        "organization_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.create_foreign_key(
        "fk_users_organization",
        "users",
        "organizations",
        ["organization_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("idx_users_org", "users", ["organization_id"], unique=False)

    # 5) API Keys: add polymorphic ownership
    op.add_column("api_keys", sa.Column("owner_type", sa.Text(), nullable=True))
    op.add_column("api_keys", sa.Column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))

    # Backfill owner_type/owner_id from legacy user_id
    op.execute("""
        UPDATE api_keys SET owner_type = 'user', owner_id = user_id
    """)
    # Keep legacy user_id column for backward compatibility but ensure owner fields are NOT NULL
    op.alter_column("api_keys", "owner_type", nullable=False)
    op.alter_column("api_keys", "owner_id", nullable=False)
    op.create_index("idx_api_keys_owner", "api_keys", ["owner_type", "owner_id"], unique=False)

    # 6) Requests: add org + owner context, make user_id nullable
    op.add_column("requests", sa.Column("organization_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column("requests", sa.Column("owner_type", sa.Text(), nullable=True))
    op.add_column("requests", sa.Column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=True))
    op.alter_column("requests", "user_id", nullable=True)
    op.create_index("idx_requests_org_day", "requests", ["organization_id", "created_at"], unique=False)

    # 7) Usage analytics: keep usage_rollups for backward compatibility; add api_usage for richer breakdown
    op.create_table(
        "api_usage",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("organization_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("owner_type", sa.Text(), nullable=False),  # 'user' | 'team'
        sa.Column("owner_id", sa.dialects.postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_id", sa.dialects.postgresql.UUID(as_uuid=True), sa.ForeignKey("api_keys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("request_count", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("prompt_tokens", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("completion_tokens", sa.BigInteger(), server_default="0", nullable=False),
        sa.Column("total_tokens", sa.BigInteger(), server_default="0", nullable=False),
        sa.UniqueConstraint("organization_id", "owner_type", "owner_id", "key_id", "day", name="uq_api_usage_all_keys"),
    )


def downgrade() -> None:
    # Drop api_usage
    op.drop_table("api_usage")

    # Requests: drop new columns and revert user_id nullability
    op.drop_index("idx_requests_org_day", table_name="requests")
    op.drop_column("requests", "owner_id")
    op.drop_column("requests", "owner_type")
    op.drop_column("requests", "organization_id")
    op.alter_column("requests", "user_id", nullable=False)

    # API Keys: drop owner polymorphic
    op.drop_index("idx_api_keys_owner", table_name="api_keys")
    op.drop_column("api_keys", "owner_id")
    op.drop_column("api_keys", "owner_type")

    # Users: drop FK/index and column
    op.drop_index("idx_users_org", table_name="users")
    op.drop_constraint("fk_users_organization", "users", type_="foreignkey")
    op.drop_column("users", "organization_id")

    # Memberships / Teams / Organizations
    op.drop_table("memberships")
    op.drop_table("teams")
    op.drop_table("organizations")

