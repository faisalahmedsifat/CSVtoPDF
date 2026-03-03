"""
Building and room configuration.
Edit this file to add/remove rooms, change default rents or gas bills.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Simple hardcoded password — change this in production via APP_PASSWORD env var
APP_PASSWORD = os.getenv("APP_PASSWORD", "billingapp2025")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production-secret-key-32chars")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "72"))

# ── Building definitions ───────────────────────────────────────────────────────
# Each building is a dict:
#   id: int          — house number printed on the bill
#   rooms: list[dict]
#     room_no: str
#     meter_no: str  — leave "" if not fixed
#     rent: float
#     gas_bill: float
#     service_charge: float

BUILDINGS = [
    {
        "id": 220,
        "label": "House 220",
        "default_gas_bill": 1080,
        "default_service_charge": 500,
        "rooms": [
            {"room_no": "1A", "meter_no": "57438", "rent": 7500},
            {"room_no": "1B", "meter_no": "57414", "rent": 7500},
            {"room_no": "2A", "meter_no": "57437", "rent": 7500},
            {"room_no": "2B", "meter_no": "57412", "rent": 7000},
            {"room_no": "2C", "meter_no": "57436", "rent": 7500},
            # 3BC is skipped in PDF generation (common meter / vacant)
            {"room_no": "4A", "meter_no": "830186", "rent": 7000},
            {"room_no": "4B", "meter_no": "57419",  "rent": 6500},
            {"room_no": "4C", "meter_no": "57440",  "rent": 7000},
            {"room_no": "5A", "meter_no": "57413",  "rent": 7000},
            {"room_no": "5B", "meter_no": "57439",  "rent": 7000},
            {"room_no": "5C", "meter_no": "57420",  "rent": 7000},
            {"room_no": "6A", "meter_no": "57417",  "rent": 7000},
            {"room_no": "6B", "meter_no": "57411",  "rent": 7000},
            {"room_no": "6C", "meter_no": "57418",  "rent": 7000},
            {"room_no": "7A", "meter_no": "10368023", "rent": 7000},
            {"room_no": "7B", "meter_no": "43256",  "rent": 7000},
        ],
    },
    {
        "id": 226,
        "label": "House 226",
        "default_gas_bill": 1080,
        "default_service_charge": 400,
        "rooms": [
            {"room_no": "1A", "meter_no": "", "rent": 5500},
            {"room_no": "1B", "meter_no": "", "rent": 7500},
            {"room_no": "2A", "meter_no": "", "rent": 0},      # no rent listed in CSV
            {"room_no": "2B", "meter_no": "", "rent": 7000},
            {"room_no": "3A", "meter_no": "", "rent": 8000},
            {"room_no": "3B", "meter_no": "", "rent": 7000},
        ],
    },
]

# Default electricity rate (BDT per unit)
DEFAULT_ELECTRICITY_RATE = float(os.getenv("ELECTRICITY_RATE", "9.0"))
DEFAULT_ELECTRICITY_RATE_HIGH = float(os.getenv("ELECTRICITY_RATE_HIGH", "10.0"))
DEFAULT_RATE_THRESHOLD = int(os.getenv("ELECTRICITY_RATE_THRESHOLD", "0"))  # 0 = no threshold


def get_room_defaults(building_id: int, room_no: str) -> dict:
    """Return the static config for a given room."""
    for bldg in BUILDINGS:
        if bldg["id"] == building_id:
            for room in bldg["rooms"]:
                if room["room_no"] == room_no:
                    return {
                        "meter_no": room.get("meter_no", ""),
                        "rent": room.get("rent", 0),
                        "gas_bill": bldg["default_gas_bill"],
                        "service_charge": bldg["default_service_charge"],
                    }
    return {}
