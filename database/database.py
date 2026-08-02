import os
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base, AssetModel, GPSReadingModel, AlertModel

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "system.db")
DATABASE_URL = f"sqlite:///{DEFAULT_DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initializes SQLite database tables."""
    os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
    Base.metadata.create_all(bind=engine)


def save_readings(df: pd.DataFrame):
    """Saves dynamic telemetry DataFrame into SQLite database."""
    init_db()
    session = SessionLocal()
    try:
        seen_assets = set()
        for _, row in df.iterrows():
            asset_id = str(row["asset_id"])
            if asset_id not in seen_assets:
                asset = session.query(AssetModel).filter(AssetModel.id == asset_id).first()
                if not asset:
                    asset = AssetModel(id=asset_id, asset_type=row.get("asset_type", "aircraft"))
                    session.add(asset)
                    session.commit()
                seen_assets.add(asset_id)
                
            reading = GPSReadingModel(
                asset_id=asset_id,
                timestamp=float(row["timestamp"]),
                latitude=float(row["latitude"]),
                longitude=float(row["longitude"]),
                altitude_ft=float(row.get("altitude_ft", 0.0)),
                speed_kts=float(row.get("speed_kts", 0.0)),
                heading_deg=float(row.get("heading_deg", 0.0)),
                acceleration_ms2=float(row.get("acceleration_ms2", 0.0)),
                data_source=str(row.get("data_source", "GPS_ADSB")),
                scenario=str(row.get("scenario", "normal")),
                is_spoofed=bool(row.get("is_spoofed", False))
            )
            session.add(reading)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def save_alerts(alerts: List[Dict[str, Any]]):
    """Saves generated alert dictionaries into SQLite database."""
    init_db()
    session = SessionLocal()
    try:
        for a in alerts:
            loc = a.get("location", (0.0, 0.0))
            alert_obj = AlertModel(
                alert_id=a["alert_id"],
                timestamp=float(a["timestamp"]),
                asset_id=a["asset_id"],
                asset_type=a["asset_type"],
                alert_type=a["alert_type"],
                severity=a["severity"],
                risk_score=float(a["risk_score"]),
                confidence=float(a.get("confidence", 0.9)),
                latitude=float(loc[0]),
                longitude=float(loc[1]),
                explanation=str(a.get("explanation", "")),
                status=a.get("status", "NEW")
            )
            session.add(alert_obj)
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


def get_all_alerts() -> List[Dict[str, Any]]:
    """Retrieves all stored alerts."""
    init_db()
    session = SessionLocal()
    try:
        alerts = session.query(AlertModel).order_by(AlertModel.timestamp.desc()).all()
        return [
            {
                "alert_id": a.alert_id,
                "timestamp": a.timestamp,
                "asset_id": a.asset_id,
                "asset_type": a.asset_type,
                "alert_type": a.alert_type,
                "severity": a.severity,
                "risk_score": a.risk_score,
                "confidence": a.confidence,
                "location": (a.latitude, a.longitude),
                "explanation": a.explanation,
                "status": a.status
            }
            for a in alerts
        ]
    finally:
        session.close()
