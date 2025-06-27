from fastapi import FastAPI, Form, Depends, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
import httpx
from typing import Optional, List
import os
from endpoint.mainIrrig import router as irrigation_router
from DB.database import Base, engine
from DB.database import engine, SessionLocal, get_session
from security import get_current_user, validate_tel
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import requests

from endpoint.mainIrrig import router as irrigation_router
from endpoint.ChatBot import router as chatbot_router
from endpoint.Users import router as users_router, router
from endpoint.disease import router as disease_router
from endpoint.recommanded import router as recommanded_router
from endpoint.ParcelleNote import router as parcelle_router
from endpoint import Catalogue

from Irrigation.WeatherCheck import check_weather_before_irrigation


# ✅ Créer les tables
Base.metadata.create_all(bind=engine)


# ✅ Initialisation de l'app (une seule fois !)
app = FastAPI()

# ✅ CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # à sécuriser en prod
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Montage des routes
app.include_router(irrigation_router, prefix="/irrigation", tags=["Irrigation"])
app.include_router(chatbot_router, prefix="/chatbot", tags=["Chatbot"])
app.include_router(users_router, prefix="/users", tags=["Users"])
app.include_router(disease_router, prefix="/disease", tags=["Disease"])
app.include_router(recommanded_router, prefix="/recommend", tags=["Recommendation"])
app.include_router(parcelle_router, prefix="/parcelles", tags=["Parcelles"])
app.include_router(Catalogue.router, prefix="/api", tags=["Catalogue Agricole"])


# ✅ Statics
AUDIO_FOLDER = os.path.abspath("audio_responses")
USER_IMAGES_FOLDER = os.path.abspath("user_images")
PLANT_IMAGES_FOLDER = os.path.abspath("storage/plants")
UPLOADS_FOLDER = os.path.abspath("storage/uploads")

os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(USER_IMAGES_FOLDER, exist_ok=True)
os.makedirs(PLANT_IMAGES_FOLDER, exist_ok=True)
os.makedirs(UPLOADS_FOLDER, exist_ok=True)

app.mount("/audio", StaticFiles(directory=AUDIO_FOLDER), name="audio")
app.mount("/user_images", StaticFiles(directory=USER_IMAGES_FOLDER), name="user_images")
app.mount("/plant_images", StaticFiles(directory=PLANT_IMAGES_FOLDER), name="plant_images")
app.mount("/uploads", StaticFiles(directory=UPLOADS_FOLDER), name="uploads")
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"

@app.get("/weather/current.json")
async def get_current_weather(
    key: str = Query(...),
    q: str = Query(...),
    aqi: str = Query("no")
):
    params = {
        "key": key,
        "q": q,
        "aqi": aqi
    }

    async with httpx.AsyncClient() as client:
        resp = await client.get(WEATHER_API_URL, params=params)

    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail="Weather API error")

    return resp.json()
GOOGLE_TRANSLATE_API_KEY = "YOUR_GOOGLE_API_KEY"

class TranslationRequest(BaseModel):
    texts: List[str]
    target_lang: str








