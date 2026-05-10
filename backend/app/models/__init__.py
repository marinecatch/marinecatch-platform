# app/models/__init__.py
#
# WHY THIS FILE EXISTS:
# Imports all models in one place.
# Alembic needs to see all models to create migrations.
# If a model is not imported here, its table won't be created.

from app.models.user import User
from app.models.fish import FishListing
from app.models.order import Order