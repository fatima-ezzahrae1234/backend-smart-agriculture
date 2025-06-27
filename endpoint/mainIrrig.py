from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from DB.models import Base, IrrigationRecord, UserDB
from DB.database import engine, get_session
from Irrigation.schemes import IrrigationInput, IrrigationOutput
from Irrigation.crud import create_irrigation_record, get_record_by_id
from Irrigation.IrrigationLogic import calculate_irrigation
from Irrigation.WeatherCheck import check_weather_before_irrigation
from security import get_current_user
import logging

Base.metadata.create_all(bind=engine)

router = APIRouter()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@router.post("/recommend-irrigation/", response_model=IrrigationOutput)
async def recommend_irrigation(data: IrrigationInput,
                               db: Session = Depends(get_session),
                               current_user: UserDB = Depends(get_current_user)):
    try:
        recommendation = calculate_irrigation(
            culture=data.culture,
            type_sol=data.type_sol,
            saison=data.saison,
            type_irrigation=data.type_irrigation
        )
        recommendation["irrigation_necessaire"] = True
        recommendation["user_id"] = current_user.id
        record = create_irrigation_record(db, recommendation)
        return {**recommendation, "id": record.id, "timestamp": record.timestamp}
    except Exception as e:
        logger.error(f"Error in recommend_irrigation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/irrigation-records/", response_model=List[IrrigationOutput])
async def get_irrigation_records(
        db: Session = Depends(get_session),
        current_user: UserDB = Depends(get_current_user)
):
    records = db.query(IrrigationRecord).filter(IrrigationRecord.user_id == current_user.id).all()
    return [IrrigationOutput.from_orm(record) for record in records]


@router.get("/check-irrigation/{record_id}")
async def check_irrigation_status(record_id: int, db: Session = Depends(get_session)):
    record = get_record_by_id(db, record_id)
    if not record:
        raise HTTPException(status_code=404, detail="Recommandation introuvable.")
    weather_ok = await check_weather_before_irrigation()
    return {"irrigation_necessaire": weather_ok}


@router.delete("/irrigation-records/{record_id}", status_code=204)
async def delete_irrigation_record(record_id: int, db: Session = Depends(get_session), current_user: UserDB = Depends(get_current_user)):
    record = db.query(IrrigationRecord).filter(
        IrrigationRecord.id == record_id,
        IrrigationRecord.user_id == current_user.id
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="Recommandation non trouvée")
    db.delete(record)
    db.commit()
    return
