from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, create_engine
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class AssetModel(Base):
    __tablename__ = "assets"
    
    id = Column(String(50), primary_key=True)
    asset_type = Column(String(50), nullable=False) # aircraft / ground_vehicle
    name = Column(String(100))
    status = Column(String(20), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)


class GPSReadingModel(Base):
    __tablename__ = "gps_readings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    asset_id = Column(String(50), ForeignKey("assets.id"), nullable=False)
    timestamp = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude_ft = Column(Float, default=0.0)
    speed_kts = Column(Float, default=0.0)
    heading_deg = Column(Float, default=0.0)
    acceleration_ms2 = Column(Float, default=0.0)
    data_source = Column(String(50), default="GPS_ADSB")
    scenario = Column(String(50), default="normal")
    is_spoofed = Column(Boolean, default=False)


class AlertModel(Base):
    __tablename__ = "alerts"
    
    alert_id = Column(String(50), primary_key=True)
    timestamp = Column(Float, nullable=False)
    asset_id = Column(String(50), ForeignKey("assets.id"), nullable=False)
    asset_type = Column(String(50), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    risk_score = Column(Float, nullable=False)
    confidence = Column(Float, default=0.9)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    explanation = Column(Text)
    status = Column(String(20), default="NEW")
    created_at = Column(DateTime, default=datetime.utcnow)
