# app/database/memory_store.py
#
# Real MarineCatch fishers, suppliers and buyers as seed data.
# This is your fake database until PostgreSQL is set up (Day 16).

from datetime import datetime
from typing import Dict, List, Optional

_users: Dict[int, dict] = {}
_listings: Dict[int, dict] = {}
_orders: Dict[int, dict] = {}
_counters = {"users": 0, "listings": 0, "orders": 0}

def _next_id(table: str) -> int:
    _counters[table] += 1
    return _counters[table]

# ── USER OPERATIONS ───────────────────────────────────────────────

def create_user(data: dict) -> dict:
    user = {
        "id": _next_id("users"),
        "created_at": datetime.utcnow(),
        "is_active": True,
        **data
    }
    _users[user["id"]] = user
    return user

def get_user_by_email(email: str) -> Optional[dict]:
    return next((u for u in _users.values()
                 if u["email"] == email), None)

def get_user_by_id(user_id: int) -> Optional[dict]:
    return _users.get(user_id)

def get_all_users() -> List[dict]:
    return list(_users.values())

# ── LISTING OPERATIONS ────────────────────────────────────────────

def create_listing(data: dict) -> dict:
    listing = {
        "id": _next_id("listings"),
        "created_at": datetime.utcnow(),
        "is_available": True,
        "total_value_kes": round(
            data["weight_kg"] * data["price_per_kg"], 2
        ),
        **data
    }
    _listings[listing["id"]] = listing
    return listing

def get_all_listings(
    species: str = None,
    landing_site: str = None
) -> List[dict]:
    results = [l for l in _listings.values()
               if l["is_available"]]
    if species:
        results = [l for l in results
                   if l["species"] == species]
    if landing_site:
        results = [l for l in results
                   if l["landing_site"] == landing_site]
    return results

def get_listing_by_id(listing_id: int) -> Optional[dict]:
    return _listings.get(listing_id)

def update_listing(listing_id: int, data: dict) -> Optional[dict]:
    if listing_id not in _listings:
        return None
    _listings[listing_id].update(data)
    return _listings[listing_id]

# ── ORDER OPERATIONS ──────────────────────────────────────────────

def create_order(data: dict) -> dict:
    order = {
        "id": _next_id("orders"),
        "created_at": datetime.utcnow(),
        "status": "pending",
        **data
    }
    _orders[order["id"]] = order
    return order

def get_orders_by_buyer(buyer_id: int) -> List[dict]:
    return [o for o in _orders.values()
            if o["buyer_id"] == buyer_id]

def get_orders_by_fisher(fisher_id: int) -> List[dict]:
    return [o for o in _orders.values()
            if o["fisher_id"] == fisher_id]

# ── REAL SEED DATA ────────────────────────────────────────────────

def seed():
    if _users:
        return  # Already seeded

    # Real fishers
    create_user({
        "name": "Abdalla Masudi",
        "email": "abdalla@kibuyuni.co.ke",
        "phone": "+254700000001",
        "role": "fisher",
        "location": "Kibuyuni",
        "business_name": None,
        "hashed_password": "hashed"
    })
    create_user({
        "name": "Bakari Usi",
        "email": "bakari@kibuyuni.co.ke",
        "phone": "+254700000002",
        "role": "fisher",
        "location": "Kibuyuni",
        "business_name": None,
        "hashed_password": "hashed"
    })
    create_user({
        "name": "Hassan Juma Mwaropia",
        "email": "hassan@ukunda.co.ke",
        "phone": "+254700000003",
        "role": "fisher",
        "location": "Ukunda",
        "business_name": None,
        "hashed_password": "hashed"
    })
    create_user({
        "name": "Shee Sahare",
        "email": "shee@mwambao.co.ke",
        "phone": "+254700000004",
        "role": "fisher",
        "location": "Mwambao",
        "business_name": None,
        "hashed_password": "hashed"
    })

    # Real suppliers
    create_user({
        "name": "Juma Riziki",
        "email": "juma@kinondo.co.ke",
        "phone": "+254700000005",
        "role": "supplier",
        "location": "Kinondo",
        "business_name": "Juma Riziki Traders",
        "hashed_password": "hashed"
    })
    create_user({
        "name": "Said Mohamed",
        "email": "said@shimoni.co.ke",
        "phone": "+254700000006",
        "role": "supplier",
        "location": "Shimoni",
        "business_name": "Rasa Fish Traders",
        "hashed_password": "hashed"
    })

    # Real buyers
    create_user({
        "name": "Neptune Hotels Procurement",
        "email": "procurement@neptunehotels.co.ke",
        "phone": "+254700000007",
        "role": "buyer",
        "location": "Diani",
        "business_name": "Holiday Resorts Limited (Neptune Hotels)",
        "hashed_password": "hashed"
    })
    create_user({
        "name": "Samaki Samaki Manager",
        "email": "orders@samakisamaki.co.ke",
        "phone": "+254700000008",
        "role": "buyer",
        "location": "Nairobi",
        "business_name": "Samaki Samaki Seafood & Jazz Restaurant",
        "hashed_password": "hashed"
    })
    create_user({
        "name": "Seafood Centre Nairobi",
        "email": "orders@seafoodcentre.co.ke",
        "phone": "+254700000009",
        "role": "buyer",
        "location": "Nairobi",
        "business_name": "Seafood Centre (Wholesaler)",
        "hashed_password": "hashed"
    })

    # Real fish listings
    create_listing({
        "fisher_id": 1,
        "fisher_name": "Abdalla Masudi",
        "species": "octopus",
        "weight_kg": 40.0,
        "price_per_kg": 650,
        "landing_site": "kibuyuni",
        "condition": "fresh",
        "description": "Fresh octopus, caught this morning",
        "harvest_date": "2025-05-07",
        "boat_number": "KM-2201"
    })
    create_listing({
        "fisher_id": 2,
        "fisher_name": "Bakari Usi",
        "species": "tuna",
        "weight_kg": 85.0,
        "price_per_kg": 780,
        "landing_site": "kibuyuni",
        "condition": "fresh",
        "description": "Yellowfin tuna, excellent quality",
        "harvest_date": "2025-05-07",
        "boat_number": "KM-1897"
    })
    create_listing({
        "fisher_id": 3,
        "fisher_name": "Hassan Juma Mwaropia",
        "species": "oysters",
        "weight_kg": 25.0,
        "price_per_kg": 900,
        "landing_site": "ukunda",
        "condition": "live",
        "description": "Live oysters, harvested at low tide",
        "harvest_date": "2025-05-07",
        "boat_number": None
    })
    create_listing({
        "fisher_id": 4,
        "fisher_name": "Shee Sahare",
        "species": "crab",
        "weight_kg": 18.0,
        "price_per_kg": 1200,
        "landing_site": "mwambao",
        "condition": "live",
        "description": "Live mud crabs, large size",
        "harvest_date": "2025-05-07",
        "boat_number": None
    })
print("MarineCatch seed data loaded")
print(f"Users loaded: {len(_users)}")
print(f"Listings loaded: {len(_listings)}")