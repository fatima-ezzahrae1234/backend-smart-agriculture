from sqlalchemy.orm import Session
from DB.models import IrrigationRecord
from datetime import datetime
import pytz

def create_irrigation_record(db: Session, data: dict):
    record = IrrigationRecord(
        culture=data["culture"],
        type_sol=data["type_sol"],
        saison=data["saison"],
        type_irrigation=data["type_irrigation"],
        frequence_irrigation=data["frequence_irrigation"],
        besoin_brut=data["besoin_brut"],
        besoin_par_seance=data["besoin_par_seance"],
        irrigation_necessaire=data.get("irrigation_necessaire", True),
        timestamp=datetime.now(pytz.utc),
        user_id = data["user_id"]
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def get_all_records(db: Session):
    return db.query(IrrigationRecord).all()

def get_record_by_id(db: Session, record_id: int):
    return db.query(IrrigationRecord).filter(IrrigationRecord.id == record_id).first()
