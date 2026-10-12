"""SQLAlchemy async models."""
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Float, Integer, Text, DateTime
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Claim(Base):
    __tablename__ = "claims"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    farmer_name: Mapped[str] = mapped_column(String(120), default="")
    father_name: Mapped[str] = mapped_column(String(120), default="")
    survey_khasra_number: Mapped[str] = mapped_column(String(60), default="")
    land_area_acres: Mapped[float | None] = mapped_column(Float, nullable=True)
    land_area_hectare: Mapped[float | None] = mapped_column(Float, nullable=True)
    village_taluka_district: Mapped[str] = mapped_column(String(160), default="")
    district_state: Mapped[str] = mapped_column(String(120), default="")
    crop_type: Mapped[str] = mapped_column(String(60), default="")
    damage_reason: Mapped[str] = mapped_column(String(120), default="")
    damage_percentage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    loss_date: Mapped[str] = mapped_column(String(40), default="")
    mobile_number: Mapped[str] = mapped_column(String(15), default="")
    language: Mapped[str] = mapped_column(String(12), default="hi-IN")
    status: Mapped[str] = mapped_column(String(20), default="draft")
    claim_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
