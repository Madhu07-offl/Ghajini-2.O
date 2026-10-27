import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Tuple
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import AuditLog, VitalsReading
from app.db.mongo import mongo_manager
from app.db.session import get_db
from app.modules.alerts.service import notify_caregivers

logger = logging.getLogger(__name__)
router = APIRouter()


# -------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------
class VitalsCreate(BaseModel):
    patient_id: Optional[int] = 1
    heart_rate_bpm: int
    blood_pressure_systolic: Optional[int] = 120
    blood_pressure_diastolic: Optional[int] = 80
    oxygen_saturation: Optional[int] = 98
    hrv_ms: Optional[int] = 45
    status: Optional[str] = None
    notes: Optional[str] = None


class VitalsResponse(BaseModel):
    id: int
    patient_id: int
    heart_rate_bpm: int
    blood_pressure_systolic: Optional[int]
    blood_pressure_diastolic: Optional[int]
    oxygen_saturation: Optional[int]
    hrv_ms: Optional[int]
    status: str
    notes: Optional[str]
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CurrentVitalsSummary(BaseModel):
    reading: VitalsResponse
    status_label: Dict[str, str]
    human_summary: Dict[str, str]
    is_critical: bool
    requires_attention: bool


def classify_vitals_status(
    bpm: int,
    systolic: Optional[int] = 120,
    diastolic: Optional[int] = 80,
    oxygen: Optional[int] = 98,
) -> str:
    """Automatically classifies heart rate & vitals status."""
    sys_val = systolic or 120
    dia_val = diastolic or 80
    o2_val = oxygen or 98

    if bpm > 130 or sys_val >= 180 or dia_val >= 120 or o2_val < 90:
        return "critical_high"
    if bpm < 45:
        return "critical_low"
    if bpm > 100 or sys_val >= 140 or dia_val >= 90:
        return "elevated"
    if bpm < 58:
        return "low"
    return "normal"


def get_vitals_translations(status: str, bpm: int) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Provides multilingual plain-language labels and summaries."""
    labels = {
        "en": "Normal" if status == "normal" else status.replace("_", " ").title(),
        "hi": "सामान्य" if status == "normal" else ("बढ़ी हुई" if status == "elevated" else "गंभीर चेतावनी"),
        "pa": "ਸਧਾਰਨ" if status == "normal" else ("ਵਧੀ ਹੋਈ" if status == "elevated" else "ਗੰਭੀਰ ਚੇਤਾਵਨੀ"),
    }
    summaries = {
        "en": f"Your heart rate is {bpm} beats per minute, which is normal and steady.",
        "hi": f"आपकी हृदय गति {bpm} धड़कन प्रति मिनट है, जो बिल्कुल सामान्य और स्थिर है।",
        "pa": f"ਤੁਹਾਡੇ ਦਿਲ ਦੀ ਧੜਕਣ {bpm} ਪ੍ਰਤੀ ਮਿੰਟ ਹੈ, ਜੋ ਕਿ ਬਿਲਕੁਲ ਸਧਾਰਨ ਅਤੇ ਠੀਕ ਹੈ।",
    }
    if "critical" in status:
        summaries["en"] = f"Abnormal heart rate of {bpm} BPM detected. Caregivers have been notified."
        summaries["hi"] = f"असामान्य हृदय गति ({bpm} BPM) पाई गई। परिवार को सूचना भेज दी गई है।"
        summaries["pa"] = f"ਅਸਧਾਰਨ ਦਿਲ ਦੀ ਧੜਕਣ ({bpm} BPM) ਮਿਲੀ ਹੈ। ਪਰਿਵਾਰ ਨੂੰ ਸੁਨੇਹਾ ਭੇਜ ਦਿੱਤਾ ਗਿਆ ਹੈ।"
    elif status == "elevated":
        summaries["en"] = f"Your heart rate is slightly elevated at {bpm} BPM. Please sit down and drink water."
        summaries["hi"] = f"आपकी हृदय गति थोड़ी बढ़ी हुई ({bpm} BPM) है। कृपया आराम से बैठें और पानी पिएं।"
        summaries["pa"] = f"ਤੁਹਾਡੇ ਦਿਲ ਦੀ ਧੜਕਣ ਥੋੜ੍ਹੀ ਵਧੀ ਹੋਈ ({bpm} BPM) ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਆਰਾਮ ਕਰੋ ਅਤੇ ਪਾਣੀ ਪੀਓ।"

    return labels, summaries


# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------
@router.post("/readings", response_model=VitalsResponse, status_code=status.HTTP_201_CREATED)
async def record_vitals(
    payload: VitalsCreate,
    db: Session = Depends(get_db),
):
    """
    Records a new vitals telemetry reading.
    If reading is critical, automatically triggers a caregiver alert and audit log.
    """
    pid = payload.patient_id or settings.DEFAULT_PATIENT_ID
    stat = payload.status or classify_vitals_status(
        bpm=payload.heart_rate_bpm,
        systolic=payload.blood_pressure_systolic,
        diastolic=payload.blood_pressure_diastolic,
        oxygen=payload.oxygen_saturation,
    )

    reading = VitalsReading(
        patient_id=pid,
        heart_rate_bpm=payload.heart_rate_bpm,
        blood_pressure_systolic=payload.blood_pressure_systolic or 120,
        blood_pressure_diastolic=payload.blood_pressure_diastolic or 80,
        oxygen_saturation=payload.oxygen_saturation or 98,
        hrv_ms=payload.hrv_ms or 45,
        status=stat,
        notes=payload.notes,
        recorded_at=datetime.utcnow(),
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)

    is_critical = "critical" in stat or stat == "arrhythmia"

    # If critical, trigger alert and audit log
    if is_critical:
        alert_msg = f"Critical cardiac reading detected: {payload.heart_rate_bpm} BPM ({stat})."
        notify_caregivers(
            patient_id=pid,
            alert_type="cardiac_anomaly",
            message=alert_msg,
            db=db,
        )

    # Persist in MongoDB for analytics
    try:
        coll = mongo_manager.get_collection("vitals")
        await coll.insert_one({
            "id": reading.id,
            "patient_id": pid,
            "heart_rate_bpm": reading.heart_rate_bpm,
            "blood_pressure": f"{reading.blood_pressure_systolic}/{reading.blood_pressure_diastolic}",
            "oxygen_saturation": reading.oxygen_saturation,
            "status": stat,
            "recorded_at": reading.recorded_at.isoformat(),
        })
    except Exception as e:
        logger.warning(f"Error persisting vitals to MongoDB: {e}")

    return reading


@router.get("/current", response_model=CurrentVitalsSummary)
def get_current_vitals(
    patient_id: int = Query(default=1),
    db: Session = Depends(get_db),
):
    """Returns the most recent vitals reading with multilingual human summary."""
    latest = (
        db.query(VitalsReading)
        .filter(VitalsReading.patient_id == patient_id)
        .order_by(VitalsReading.recorded_at.desc())
        .first()
    )

    if not latest:
        # Create baseline reading if none exists
        latest = VitalsReading(
            patient_id=patient_id,
            heart_rate_bpm=72,
            blood_pressure_systolic=120,
            blood_pressure_diastolic=80,
            oxygen_saturation=98,
            hrv_ms=48,
            status="normal",
            notes="Baseline reading",
            recorded_at=datetime.utcnow(),
        )
        db.add(latest)
        db.commit()
        db.refresh(latest)

    labels, summaries = get_vitals_translations(latest.status, latest.heart_rate_bpm)
    is_crit = "critical" in latest.status or latest.status == "arrhythmia"

    return CurrentVitalsSummary(
        reading=VitalsResponse.model_validate(latest),
        status_label=labels,
        human_summary=summaries,
        is_critical=is_crit,
        requires_attention=is_crit or latest.status == "elevated",
    )


@router.get("/history", response_model=List[VitalsResponse])
def get_vitals_history(
    patient_id: int = Query(default=1),
    limit: int = Query(default=20, le=100),
    db: Session = Depends(get_db),
):
    """Returns historical vitals records for trend analysis."""
    readings = (
        db.query(VitalsReading)
        .filter(VitalsReading.patient_id == patient_id)
        .order_by(VitalsReading.recorded_at.desc())
        .limit(limit)
        .all()
    )
    return readings


@router.get("/ecg-live")
def get_live_ecg_waveform(
    bpm: Optional[int] = Query(default=72),
    samples: int = Query(default=120, le=300),
):
    """
    Generates realistic, mathematical P-Q-R-S-T electrocardiogram data points
    based on target BPM for real-time Flutter waveform charting.
    """
    effective_bpm = max(40, min(180, bpm or 72))
    points = []
    # 1 cardiac cycle duration in seconds = 60 / bpm
    cycle_period = 60.0 / effective_bpm

    for i in range(samples):
        t = (i * 0.02) % cycle_period
        # Standard synthetic P-Q-R-S-T voltage curve
        y = 0.0
        # Baseline noise
        y += 0.02 * math.sin(2 * math.pi * t * 5)
        # P-wave
        if 0.1 <= t < 0.2:
            y += 0.15 * math.sin(math.pi * (t - 0.1) / 0.1)
        # Q-dip
        elif 0.22 <= t < 0.25:
            y -= 0.18 * math.sin(math.pi * (t - 0.22) / 0.03)
        # R-peak
        elif 0.25 <= t < 0.29:
            y += 1.35 * math.sin(math.pi * (t - 0.25) / 0.04)
        # S-dip
        elif 0.29 <= t < 0.33:
            y -= 0.35 * math.sin(math.pi * (t - 0.29) / 0.04)
        # T-wave
        elif 0.40 <= t < 0.55:
            y += 0.28 * math.sin(math.pi * (t - 0.40) / 0.15)

        points.append(round(y, 4))

    return {
        "bpm": effective_bpm,
        "sample_interval_ms": 20,
        "waveform": points,
    }


@router.post("/simulate")
async def simulate_vitals_scenario(
    scenario: Literal["normal", "elevated", "critical_tachycardia", "bradycardia"],
    patient_id: int = Query(default=1),
    db: Session = Depends(get_db),
):
    """Demo shortcut to simulate cardiac conditions for presentations."""
    presets = {
        "normal": {"bpm": 74, "sys": 120, "dia": 80, "o2": 98, "hrv": 52, "notes": "Normal resting rhythm"},
        "elevated": {"bpm": 106, "sys": 142, "dia": 92, "o2": 96, "hrv": 35, "notes": "Post-walk elevated rate"},
        "critical_tachycardia": {"bpm": 144, "sys": 165, "dia": 105, "o2": 92, "hrv": 18, "notes": "Acute tachycardia spike"},
        "bradycardia": {"bpm": 42, "sys": 105, "dia": 68, "o2": 94, "hrv": 24, "notes": "Abnormal bradycardia"},
    }
    cfg = presets[scenario]
    return await record_vitals(
        VitalsCreate(
            patient_id=patient_id,
            heart_rate_bpm=cfg["bpm"],
            blood_pressure_systolic=cfg["sys"],
            blood_pressure_diastolic=cfg["dia"],
            oxygen_saturation=cfg["o2"],
            hrv_ms=cfg["hrv"],
            notes=cfg["notes"],
        ),
        db=db,
    )
