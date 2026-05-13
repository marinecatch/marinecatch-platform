"""Fix all remaining enum values to lowercase

Revision ID: 74889c11862c
Revises: 7931e7a85aea
Create Date: 2026-05-13 15:23:00.359968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74889c11862c'
down_revision: Union[str, Sequence[str], None] = '7931e7a85aea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ownershiptype
    op.execute("ALTER TYPE ownershiptype RENAME TO ownershiptype_old")
    op.execute("""CREATE TYPE ownershiptype AS ENUM (
        'marketplace', 'marinecatch_owned', 'consignment', 'contract_reserved'
    )""")
    op.execute("""
        ALTER TABLE inventory_lots
            ALTER COLUMN ownership_type DROP DEFAULT,
            ALTER COLUMN ownership_type TYPE ownershiptype
            USING CASE ownership_type::text
                WHEN 'MARKETPLACE'       THEN 'marketplace'::ownershiptype
                WHEN 'MARINECATCH_OWNED' THEN 'marinecatch_owned'::ownershiptype
                WHEN 'CONSIGNMENT'       THEN 'consignment'::ownershiptype
                WHEN 'CONTRACT_RESERVED' THEN 'contract_reserved'::ownershiptype
                ELSE 'marketplace'::ownershiptype
            END,
            ALTER COLUMN ownership_type SET DEFAULT 'marketplace'::ownershiptype
    """)
    op.execute("DROP TYPE ownershiptype_old")

    # productform
    op.execute("ALTER TYPE productform RENAME TO productform_old")
    op.execute("""CREATE TYPE productform AS ENUM (
        'whole_ungutted', 'whole_gutted', 'headed_gutted',
        'fillet', 'dried', 'smoked', 'live', 'other'
    )""")
    op.execute("""
        ALTER TABLE inventory_lots
            ALTER COLUMN product_form DROP DEFAULT,
            ALTER COLUMN product_form TYPE productform
            USING CASE product_form::text
                WHEN 'WHOLE_UNGUTTED' THEN 'whole_ungutted'::productform
                WHEN 'WHOLE_GUTTED'   THEN 'whole_gutted'::productform
                WHEN 'HEADED_GUTTED'  THEN 'headed_gutted'::productform
                WHEN 'FILLET'         THEN 'fillet'::productform
                WHEN 'DRIED'          THEN 'dried'::productform
                WHEN 'SMOKED'         THEN 'smoked'::productform
                WHEN 'LIVE'           THEN 'live'::productform
                WHEN 'OTHER'          THEN 'other'::productform
                ELSE 'whole_ungutted'::productform
            END,
            ALTER COLUMN product_form SET DEFAULT 'whole_ungutted'::productform
    """)
    op.execute("DROP TYPE productform_old")

    # qualitygrade
    op.execute("ALTER TYPE qualitygrade RENAME TO qualitygrade_old")
    op.execute("""CREATE TYPE qualitygrade AS ENUM (
        'A', 'B', 'C', 'pending'
    )""")
    op.execute("""
        ALTER TABLE inventory_lots
            ALTER COLUMN grade DROP DEFAULT,
            ALTER COLUMN grade TYPE qualitygrade
            USING CASE grade::text
                WHEN 'A'       THEN 'A'::qualitygrade
                WHEN 'B'       THEN 'B'::qualitygrade
                WHEN 'C'       THEN 'C'::qualitygrade
                WHEN 'PENDING' THEN 'pending'::qualitygrade
                ELSE 'pending'::qualitygrade
            END,
            ALTER COLUMN grade SET DEFAULT 'pending'::qualitygrade
    """)
    op.execute("DROP TYPE qualitygrade_old")

    # lotcondition
    op.execute("ALTER TYPE lotcondition RENAME TO lotcondition_old")
    op.execute("""CREATE TYPE lotcondition AS ENUM (
        'fresh', 'frozen', 'dried', 'live', 'processed'
    )""")
    op.execute("""
        ALTER TABLE inventory_lots
            ALTER COLUMN condition DROP DEFAULT,
            ALTER COLUMN condition TYPE lotcondition
            USING CASE condition::text
                WHEN 'FRESH'     THEN 'fresh'::lotcondition
                WHEN 'FROZEN'    THEN 'frozen'::lotcondition
                WHEN 'DRIED'     THEN 'dried'::lotcondition
                WHEN 'LIVE'      THEN 'live'::lotcondition
                WHEN 'PROCESSED' THEN 'processed'::lotcondition
                ELSE 'fresh'::lotcondition
            END,
            ALTER COLUMN condition SET DEFAULT 'fresh'::lotcondition
    """)
    op.execute("DROP TYPE lotcondition_old")

    # fulfillmentmode
    op.execute("ALTER TYPE fulfillmentmode RENAME TO fulfillmentmode_old")
    op.execute("""CREATE TYPE fulfillmentmode AS ENUM (
        'self_pickup', 'seller_delivery',
        'third_party_logistics', 'marinecatch_fulfillment'
    )""")
    op.execute("""
        ALTER TABLE inventory_lots
            ALTER COLUMN fulfillment_mode DROP DEFAULT,
            ALTER COLUMN fulfillment_mode TYPE fulfillmentmode
            USING CASE fulfillment_mode::text
                WHEN 'SELF_PICKUP'             THEN 'self_pickup'::fulfillmentmode
                WHEN 'SELLER_DELIVERY'         THEN 'seller_delivery'::fulfillmentmode
                WHEN 'THIRD_PARTY_LOGISTICS'   THEN 'third_party_logistics'::fulfillmentmode
                WHEN 'MARINECATCH_FULFILLMENT' THEN 'marinecatch_fulfillment'::fulfillmentmode
                ELSE 'self_pickup'::fulfillmentmode
            END,
            ALTER COLUMN fulfillment_mode SET DEFAULT 'self_pickup'::fulfillmentmode
    """)
    op.execute("DROP TYPE fulfillmentmode_old")

    # logisticsresponsibility
    op.execute("ALTER TYPE logisticsresponsibility RENAME TO logisticsresponsibility_old")
    op.execute("""CREATE TYPE logisticsresponsibility AS ENUM (
        'buyer', 'seller', 'marinecatch', 'third_party'
    )""")
    op.execute("""
        ALTER TABLE inventory_lots
            ALTER COLUMN logistics_responsibility DROP DEFAULT,
            ALTER COLUMN logistics_responsibility TYPE logisticsresponsibility
            USING CASE logistics_responsibility::text
                WHEN 'BUYER'       THEN 'buyer'::logisticsresponsibility
                WHEN 'SELLER'      THEN 'seller'::logisticsresponsibility
                WHEN 'MARINECATCH' THEN 'marinecatch'::logisticsresponsibility
                WHEN 'THIRD_PARTY' THEN 'third_party'::logisticsresponsibility
                ELSE 'buyer'::logisticsresponsibility
            END,
            ALTER COLUMN logistics_responsibility SET DEFAULT 'buyer'::logisticsresponsibility
    """)
    op.execute("DROP TYPE logisticsresponsibility_old")


def downgrade() -> None:
    pass
