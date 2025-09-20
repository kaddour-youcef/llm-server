from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_add_expires_at_api_keys"
down_revision = "0002_user_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "api_keys",
        sa.Column("expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("api_keys", "expires_at")

