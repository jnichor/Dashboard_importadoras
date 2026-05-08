from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, Text, Boolean,
    DateTime, ForeignKey, CheckConstraint, UniqueConstraint,
    Index,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class Business(Base):
    __tablename__ = "businesses"
    __table_args__ = (
        CheckConstraint("rating >= 0 AND rating <= 5", name="ck_rating_range"),
        CheckConstraint("review_count >= 0", name="ck_review_count_positive"),
        UniqueConstraint("place_id", name="uq_place_id"),
        Index("idx_businesses_district", "district"),
        Index("idx_businesses_prospect", "prospect_qualifies"),
        Index("idx_businesses_scraped_at", "scraped_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(String, nullable=False)
    name = Column(String, nullable=False)
    address = Column(Text, nullable=True)
    district = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    website_url = Column(Text, nullable=True)
    has_website = Column(Boolean, nullable=False, default=False)
    rating = Column(Float, nullable=True)
    review_count = Column(Integer, nullable=False, default=0)
    category = Column(String, nullable=True)
    opening_hours = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    oldest_review_date = Column(String, nullable=True)
    antiguedad_flag = Column(
        String, nullable=False, default="no_determinada"
    )
    prospect_qualifies = Column(Integer, nullable=True)
    disqualify_reason = Column(Text, nullable=True)
    scraped_at = Column(String, nullable=False)

    website_check = relationship("WebsiteCheck", back_populates="business", uselist=False)


class WebsiteCheck(Base):
    __tablename__ = "website_checks"
    __table_args__ = (
        UniqueConstraint("place_id", name="uq_wc_place_id"),
        Index("idx_website_checks_place_id", "place_id"),
        Index("idx_website_checks_verdict", "verdict"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    business_id = Column(Integer, ForeignKey("businesses.id"), nullable=False)
    place_id = Column(String, nullable=False)
    http_status = Column(Integer, nullable=True)
    copyright_year = Column(Integer, nullable=True)
    wayback_last_capture = Column(String, nullable=True)
    verdict = Column(String, nullable=False)
    checked_at = Column(String, nullable=False)

    business = relationship("Business", back_populates="website_check")


class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(String, nullable=False)
    completed_at = Column(String, nullable=True)
    districts_queried = Column(Text, nullable=False)
    keywords_used = Column(Text, nullable=False)
    businesses_found = Column(Integer, nullable=True)
    errors = Column(Integer, nullable=True)


class CallOutcome(Base):
    """Resultado del seguimiento de llamadas a un negocio.

    contacted: 'no_llamado' | 'contesto' | 'no_contesto'
    response:  'acepto' | 'rechazo' | 'pendiente' | None  (solo si contacted='contesto')
    """
    __tablename__ = "call_outcomes"
    __table_args__ = (
        UniqueConstraint("place_id", name="uq_co_place_id"),
        Index("idx_call_outcomes_place_id", "place_id"),
        Index("idx_call_outcomes_contacted", "contacted"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    place_id = Column(String, ForeignKey("businesses.place_id"), nullable=False)
    contacted = Column(String, nullable=False, default="no_llamado")
    response = Column(String, nullable=True)
    called_at = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    updated_at = Column(String, nullable=False)
