"""
SQLAlchemy ORM models.
Designed to be portable: SQLite for development, PostgreSQL for production.
"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base


class MonthRecord(Base):
    __tablename__ = "month_records"

    id = Column(Integer, primary_key=True, index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)          # 1–12
    electricity_rate = Column(Float, default=9.0)    # BDT per unit (default tier)
    rate_threshold_units = Column(Integer, default=0)  # if units_used > this, apply high_rate
    electricity_rate_high = Column(Float, default=10.0)  # BDT per unit above threshold
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    rooms = relationship("RoomReading", back_populates="month_record", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("year", "month", name="uq_year_month"),)

    def __repr__(self):
        return f"<MonthRecord {self.year}-{self.month:02d}>"


class RoomReading(Base):
    __tablename__ = "room_readings"

    id = Column(Integer, primary_key=True, index=True)
    month_record_id = Column(Integer, ForeignKey("month_records.id"), nullable=False)
    building_num = Column(Integer, nullable=False)   # 220 or 226
    room_no = Column(String(10), nullable=False)     # e.g. "1A", "7B"
    meter_no = Column(String(20), default="")
    previous_units = Column(Float, default=0)
    present_units = Column(Float, default=0)
    rent = Column(Float, default=0)
    gas_bill = Column(Float, default=1080)
    service_charge = Column(Float, default=500)
    previous_due = Column(Float, default=0)
    paid = Column(Float, default=0)
    comments = Column(String(500), default="")

    month_record = relationship("MonthRecord", back_populates="rooms")

    __table_args__ = (
        UniqueConstraint("month_record_id", "building_num", "room_no", name="uq_room_month"),
    )

    @property
    def units_used(self) -> float:
        return max(0.0, self.present_units - self.previous_units)

    def electric_bill(self, rate: float, high_rate: float, threshold: int) -> float:
        u = self.units_used
        if threshold > 0 and u > threshold:
            return threshold * rate + (u - threshold) * high_rate
        return u * rate

    def total_bill(self, rate: float, high_rate: float, threshold: int) -> float:
        return (
            self.electric_bill(rate, high_rate, threshold)
            + self.gas_bill
            + self.service_charge
            + self.rent
            + self.previous_due
            - self.paid
        )

    def __repr__(self):
        return f"<RoomReading bldg={self.building_num} room={self.room_no}>"
