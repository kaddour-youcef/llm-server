from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_user_auth"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add password_hash and status to users
    op.add_column("users", sa.Column("password_hash", sa.Text(), nullable=True))
    op.add_column("users", sa.Column("status", sa.Text(), nullable=False, server_default="pending"))


def downgrade() -> None:
    op.drop_column("users", "status")
    op.drop_column("users", "password_hash")

