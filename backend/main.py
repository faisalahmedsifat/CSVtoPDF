"""
FastAPI application — Building Bill Manager
Endpoints:
  POST /api/auth/login           — get JWT token
  GET  /api/buildings            — building + room config
  GET  /api/months               — list all months
  POST /api/months               — create a new month (seeds carry-forward)
  GET  /api/months/{year}/{month}
  PUT  /api/months/{year}/{month}/rate    — update electricity rate settings
  GET  /api/months/{year}/{month}/rooms
  PUT  /api/months/{year}/{month}/rooms  — bulk-save room readings
  POST /api/months/{year}/{month}/generate-pdf
"""
import os
import datetime
import calendar
from typing import Annotated

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles

from jose import JWTError, jwt
import bcrypt as _bcrypt
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .database import engine, get_db, Base
from . import models
from .config import (
    APP_PASSWORD,
    SECRET_KEY,
    TOKEN_EXPIRE_HOURS,
    BUILDINGS,
    DEFAULT_ELECTRICITY_RATE,
    DEFAULT_ELECTRICITY_RATE_HIGH,
    DEFAULT_RATE_THRESHOLD,
    get_room_defaults,
)
from .pdf_gen import generate_pdf_for_month

# ── Create tables ──────────────────────────────────────────────────────────────
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Building Bill Manager", version="1.0.0")

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth ───────────────────────────────────────────────────────────────────────
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
ALGORITHM = "HS256"

HASHED_PASSWORD = _bcrypt.hashpw(APP_PASSWORD.encode(), _bcrypt.gensalt())


def create_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=TOKEN_EXPIRE_HOURS)
    to_encode["exp"] = expire
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


# ── Pydantic schemas ───────────────────────────────────────────────────────────
class Token(BaseModel):
    access_token: str
    token_type: str


class RoomReadingIn(BaseModel):
    building_num: int
    room_no: str
    meter_no: str = ""
    previous_units: float = 0
    present_units: float = 0
    rent: float = 0
    gas_bill: float = 1080
    service_charge: float = 500
    previous_due: float = 0
    paid: float = 0
    comments: str = ""


class RateSettingsIn(BaseModel):
    electricity_rate: float
    electricity_rate_high: float
    rate_threshold_units: int


class MonthCreateIn(BaseModel):
    year: int
    month: int  # 1–12


# ── Helper: compute derived fields for a room reading ─────────────────────────
def _room_to_dict(r: models.RoomReading, rec: models.MonthRecord) -> dict:
    units = r.units_used
    eb = r.electric_bill(rec.electricity_rate, rec.electricity_rate_high, rec.rate_threshold_units)
    tb = r.total_bill(rec.electricity_rate, rec.electricity_rate_high, rec.rate_threshold_units)
    return {
        "id": r.id,
        "building_num": r.building_num,
        "room_no": r.room_no,
        "meter_no": r.meter_no,
        "previous_units": r.previous_units,
        "present_units": r.present_units,
        "units_used": units,
        "electric_bill": round(eb, 2),
        "gas_bill": r.gas_bill,
        "service_charge": r.service_charge,
        "rent": r.rent,
        "previous_due": r.previous_due,
        "paid": r.paid,
        "comments": r.comments,
        "total_bill": round(tb, 2),
    }


# ══════════════════════════════════════════════════════════════════════════════
# Auth routes
# ══════════════════════════════════════════════════════════════════════════════
@app.post("/api/auth/login", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    if not _bcrypt.checkpw(form_data.password.encode(), HASHED_PASSWORD):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Wrong password")
    token = create_token({"sub": "admin"})
    return {"access_token": token, "token_type": "bearer"}


# ══════════════════════════════════════════════════════════════════════════════
# Building config route
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/buildings")
def get_buildings(user: str = Depends(get_current_user)):
    return BUILDINGS


# ══════════════════════════════════════════════════════════════════════════════
# Month routes
# ══════════════════════════════════════════════════════════════════════════════
@app.get("/api/months")
def list_months(db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    records = db.query(models.MonthRecord).order_by(
        models.MonthRecord.year.desc(), models.MonthRecord.month.desc()
    ).all()
    return [
        {
            "year": r.year,
            "month": r.month,
            "month_name": calendar.month_name[r.month],
            "electricity_rate": r.electricity_rate,
            "electricity_rate_high": r.electricity_rate_high,
            "rate_threshold_units": r.rate_threshold_units,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@app.post("/api/months", status_code=201)
def create_month(body: MonthCreateIn, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    existing = db.query(models.MonthRecord).filter_by(year=body.year, month=body.month).first()
    if existing:
        raise HTTPException(400, f"{calendar.month_name[body.month]} {body.year} already exists.")

    # Find previous month's record for carry-forward
    prev_date = datetime.date(body.year, body.month, 1) - datetime.timedelta(days=1)
    prev_record = db.query(models.MonthRecord).filter_by(
        year=prev_date.year, month=prev_date.month
    ).first()

    new_record = models.MonthRecord(
        year=body.year,
        month=body.month,
        electricity_rate=DEFAULT_ELECTRICITY_RATE,
        electricity_rate_high=DEFAULT_ELECTRICITY_RATE_HIGH,
        rate_threshold_units=DEFAULT_RATE_THRESHOLD,
    )
    db.add(new_record)
    db.flush()  # get new_record.id

    # Seed rooms from config + carry-forward previous present_units → this month's previous_units
    prev_readings: dict[tuple, float] = {}
    if prev_record:
        for pr in prev_record.rooms:
            prev_readings[(pr.building_num, pr.room_no)] = pr.present_units

    for bldg in BUILDINGS:
        for room in bldg["rooms"]:
            defaults = get_room_defaults(bldg["id"], room["room_no"])
            key = (bldg["id"], room["room_no"])
            prev_u = prev_readings.get(key, 0.0)
            rr = models.RoomReading(
                month_record_id=new_record.id,
                building_num=bldg["id"],
                room_no=room["room_no"],
                meter_no=defaults.get("meter_no", ""),
                previous_units=prev_u,
                present_units=prev_u,  # start equal; user updates present
                rent=defaults.get("rent", 0),
                gas_bill=defaults.get("gas_bill", 1080),
                service_charge=defaults.get("service_charge", 500),
            )
            db.add(rr)

    db.commit()
    db.refresh(new_record)
    return {"year": new_record.year, "month": new_record.month, "id": new_record.id}


@app.get("/api/months/{year}/{month}")
def get_month(year: int, month: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    rec = db.query(models.MonthRecord).filter_by(year=year, month=month).first()
    if not rec:
        raise HTTPException(404, "Month not found")
    return {
        "year": rec.year,
        "month": rec.month,
        "month_name": calendar.month_name[rec.month],
        "electricity_rate": rec.electricity_rate,
        "electricity_rate_high": rec.electricity_rate_high,
        "rate_threshold_units": rec.rate_threshold_units,
        "rooms": [_room_to_dict(r, rec) for r in rec.rooms],
    }


@app.put("/api/months/{year}/{month}/rate")
def update_rate(
    year: int, month: int, body: RateSettingsIn,
    db: Session = Depends(get_db), user: str = Depends(get_current_user)
):
    rec = db.query(models.MonthRecord).filter_by(year=year, month=month).first()
    if not rec:
        raise HTTPException(404, "Month not found")
    rec.electricity_rate = body.electricity_rate
    rec.electricity_rate_high = body.electricity_rate_high
    rec.rate_threshold_units = body.rate_threshold_units
    rec.updated_at = datetime.datetime.utcnow()
    db.commit()
    return {"ok": True}


@app.get("/api/months/{year}/{month}/rooms")
def get_rooms(year: int, month: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    rec = db.query(models.MonthRecord).filter_by(year=year, month=month).first()
    if not rec:
        raise HTTPException(404, "Month not found")
    return [_room_to_dict(r, rec) for r in rec.rooms]


@app.put("/api/months/{year}/{month}/rooms")
def update_rooms(
    year: int,
    month: int,
    rooms: list[RoomReadingIn],
    db: Session = Depends(get_db),
    user: str = Depends(get_current_user),
):
    rec = db.query(models.MonthRecord).filter_by(year=year, month=month).first()
    if not rec:
        raise HTTPException(404, "Month not found")

    for incoming in rooms:
        rr = (
            db.query(models.RoomReading)
            .filter_by(month_record_id=rec.id, building_num=incoming.building_num, room_no=incoming.room_no)
            .first()
        )
        if not rr:
            rr = models.RoomReading(month_record_id=rec.id, building_num=incoming.building_num, room_no=incoming.room_no)
            db.add(rr)

        rr.meter_no = incoming.meter_no
        rr.previous_units = incoming.previous_units
        rr.present_units = incoming.present_units
        rr.rent = incoming.rent
        rr.gas_bill = incoming.gas_bill
        rr.service_charge = incoming.service_charge
        rr.previous_due = incoming.previous_due
        rr.paid = incoming.paid
        rr.comments = incoming.comments

    rec.updated_at = datetime.datetime.utcnow()
    db.commit()
    db.refresh(rec)
    return [_room_to_dict(r, rec) for r in rec.rooms]


@app.post("/api/months/{year}/{month}/generate-pdf")
def generate_pdf(year: int, month: int, db: Session = Depends(get_db), user: str = Depends(get_current_user)):
    rec = db.query(models.MonthRecord).filter_by(year=year, month=month).first()
    if not rec:
        raise HTTPException(404, "Month not found")

    rooms_data = [_room_to_dict(r, rec) for r in rec.rooms]
    pdf_bytes = generate_pdf_for_month(rooms_data, year, month)

    month_name = calendar.month_name[month]
    filename = f"bills_{month_name}_{year}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ── Serve frontend build (production) ─────────────────────────────────────────
FRONTEND_DIST = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
