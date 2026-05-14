"""Fix userrole enum to lowercase

Revision ID: c8c731420c36
Revises: 49f0691c4524
Create Date: 2026-05-14 11:02:31.763789

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c8c731420c36'
down_revision: Union[str, Sequence[str], None] = '49f0691c4524'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("""
        CREATE TYPE userrole AS ENUM (
            'fisher',
            'supplier',
            'buyer',
            'admin',
            'partner',
            'coordinator'
        )
    """)
    op.execute("""
        ALTER TABLE users
            ALTER COLUMN role DROP DEFAULT,
            ALTER COLUMN role TYPE userrole
            USING CASE role::text
                WHEN 'FISHER'      THEN 'fisher'::userrole
                WHEN 'SUPPLIER'    THEN 'supplier'::userrole
                WHEN 'BUYER'       THEN 'buyer'::userrole
                WHEN 'ADMIN'       THEN 'admin'::userrole
                WHEN 'partner'     THEN 'partner'::userrole
                WHEN 'coordinator' THEN 'coordinator'::userrole
                ELSE 'fisher'::userrole
            END,
            ALTER COLUMN role SET DEFAULT 'fisher'::userrole
    """)
    op.execute("DROP TYPE userrole_old")


def downgrade() -> None:
    op.execute("ALTER TYPE userrole RENAME TO userrole_new")
    op.execute("""
        CREATE TYPE userrole AS ENUM (
            'FISHER',
            'SUPPLIER',
            'BUYER',
            'ADMIN',
            'partner',
            'coordinator'
        )
    """)
    op.execute("""
        ALTER TABLE users
            ALTER COLUMN role DROP DEFAULT,
            ALTER COLUMN role TYPE userrole
            USING CASE role::text
                WHEN 'fisher'      THEN 'FISHER'::userrole
                WHEN 'supplier'    THEN 'SUPPLIER'::userrole
                WHEN 'buyer'       THEN 'BUYER'::userrole
                WHEN 'admin'       THEN 'ADMIN'::userrole
                WHEN 'partner'     THEN 'partner'::userrole
                WHEN 'coordinator' THEN 'coordinator'::userrole
                ELSE 'FISHER'::userrole
            END,
            ALTER COLUMN role SET DEFAULT 'FISHER'::userrole
    """)
    op.execute("DROP TYPE userrole_new")