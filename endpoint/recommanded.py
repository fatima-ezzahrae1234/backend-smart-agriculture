import datetime
from fastapi import HTTPException, Depends, APIRouter
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ai.RecCultures.recommanders import recommender_model
from DB.database import get_session
from DB.models import CropRecommendation, UserDB
from security import get_current_user

router = APIRouter()


class SoilDetails(BaseModel):
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float


class CropRecommendationOutput(BaseModel):
    id: int
    N: float
    P: float
    K: float
    temperature: float
    humidity: float
    ph: float
    rainfall: float
    recommended_crop: str
    timestamp: datetime.datetime

    class Config:
        orm_mode = True  # <<-- This is the key addition


@router.post("/recommend-crop/")
async def recommend_crop(
    soil_details: SoilDetails,
    session: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user)
):
    try:
        print("Received soil details:", soil_details)
        details = list(soil_details.dict().values())
        print("Details list for model:", details)

        recommended_crop = recommender_model(details)
        print("Recommended crop:", recommended_crop)

        crop_recommendation = CropRecommendation(
            N=soil_details.N,
            temperature=soil_details.temperature,
            P=soil_details.P,
            humidity=soil_details.humidity,
            K=soil_details.K,
            ph=soil_details.ph,
            rainfall=soil_details.rainfall,
            recommended_crop=recommended_crop,
            user_id=user.id
        )

        session.add(crop_recommendation)
        session.commit()
        session.refresh(crop_recommendation)
        print("Recommendation saved to DB with id:", crop_recommendation.id)

        return {"recommended_crop": recommended_crop}
    except Exception as e:
        import traceback
        traceback.print_exc()  # print full error stack trace in the console
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/crop-recommendations/", response_model=list[CropRecommendationOutput])
async def get_crop_recommendations(
    db: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user)
):
    try:
        recommendations = db.query(CropRecommendation).filter(CropRecommendation.user_id == user.id).all()
        return recommendations  # Now FastAPI will convert ORM models to Pydantic automatically
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
