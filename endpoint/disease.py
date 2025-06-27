import datetime
import json
from pathlib import Path
from uuid import uuid4
from PIL import Image
from fastapi import UploadFile, File, HTTPException, Depends, Form, APIRouter, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ai.DetecMaladie.disease_prediction import PlantDiseaseModel
from DB.database import get_session
from DB.models import ImagePrediction, UserDB
from security import get_current_user

router = APIRouter()


@router.post("/predict-disease/")
async def predict_disease(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user)
):
    try:
        Path("./storage/plants").mkdir(parents=True, exist_ok=True)

        file_name = f"{uuid4()}.jpg"
        file_location = f"storage/plants/{file_name}"

        with open(file_location, "wb") as buffer:
            buffer.write(file.file.read())

        image = Image.open(file_location).convert("RGB")
        model = PlantDiseaseModel()
        predicted_disease = model.predict(image)

        image_prediction = ImagePrediction(
            filename=file.filename,
            prediction=predicted_disease,
            file_path=file_name,
            user_id=user.id
        )
        session.add(image_prediction)
        session.commit()
        session.refresh(image_prediction)

        return {
            "prediction_id": image_prediction.id,
            "predicted_disease": predicted_disease
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/criteres-disponibles/")
async def get_criteres_disponibles(
    prediction_id: int,
    session: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user)
):
    prediction = session.query(ImagePrediction).filter_by(id=prediction_id, user_id=user.id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prédiction non trouvée")

    disease_full = prediction.prediction
    if "___" not in disease_full:
        raise HTTPException(status_code=400, detail="Format de prédiction invalide")

    plant, disease = [part.strip().replace("_", " ") for part in disease_full.split("___")]

    with open("DB/versionFinale.json", encoding="utf-8") as f:
        all_data = json.load(f)

    entries = [
        e for e in all_data
        if e.get("Plant") and e.get("Disease")
        and e["Plant"].strip().lower() == plant.lower()
        and e["Disease"].strip().lower() == disease.lower()
    ]

    gravites = sorted(set(e["Gravité ciblée"] for e in entries if e.get("Gravité ciblée")))
    stades = sorted(set(e["Stade recommandé"] for e in entries if e.get("Stade recommandé")))
    dars = sorted(set(str(e["DAR"]).strip() for e in entries if e.get("DAR")))

    return {
        "gravites": gravites,
        "stades": stades,
        "dars": dars,
        "all_matieres": entries
    }


@router.post("/recommend-matiere/")
async def recommend_matiere(
    prediction_id: int = Form(...),
    critere_gravite: str = Form(...),
    critere_stade: str = Form(...),
    critere_dar: str = Form(...),
    session: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user)
):
    prediction = session.query(ImagePrediction).filter_by(id=prediction_id, user_id=user.id).first()
    if not prediction:
        raise HTTPException(status_code=404, detail="Prédiction non trouvée")

    disease_full = prediction.prediction
    if "___" not in disease_full:
        raise HTTPException(status_code=400, detail="Format de prédiction invalide")

    plant, disease = [part.strip().replace("_", " ") for part in disease_full.split("___")]

    with open("DB/versionFinale.json", encoding="utf-8") as f:
        all_data = json.load(f)

    possibles = [
        e for e in all_data
        if e.get("Plant") and e.get("Disease")
        and e["Plant"].strip().lower() == plant.lower()
        and e["Disease"].strip().lower() == disease.lower()
    ]

    match = next(
        (
            e for e in possibles
            if e.get("Gravité ciblée") == critere_gravite
            and e.get("Stade recommandé") == critere_stade
            and str(e.get("DAR")).strip() == critere_dar
        ),
        None
    )

    if not match:
        raise HTTPException(status_code=404, detail="Aucune matière active ne correspond à ces critères")

    matiere = match["matiéres actives"]

    prediction.plant = plant
    prediction.disease = disease
    prediction.recommended_matiere = matiere
    prediction.critere_gravite = critere_gravite
    prediction.critere_stade = critere_stade
    prediction.critere_dar = critere_dar
    session.commit()

    return {
        "recommended_matiere": matiere,
        "plant": plant,
        "disease": disease
    }


class ImagePredictionOutput(BaseModel):
    id: int
    filename: str
    prediction: str
    file_path: str
    timestamp: datetime.datetime
    plant: str | None = None
    disease: str | None = None
    recommended_matiere: str | None = None
    critere_gravite: str | None = None
    critere_stade: str | None = None
    critere_dar: str | None = None
    image_url: str | None = None  # ✅ Add this field

    class Config:
        orm_mode = True

    @staticmethod
    def from_orm_custom(pred: ImagePrediction, request: Request) -> "ImagePredictionOutput":
        base_url = str(request.base_url).rstrip("/")
        return ImagePredictionOutput(
            id=pred.id,
            filename=pred.filename,
            prediction=pred.prediction,
            file_path=pred.file_path,
            timestamp=pred.timestamp,
            plant=pred.plant,
            disease=pred.disease,
            recommended_matiere=pred.recommended_matiere,
            critere_gravite=pred.critere_gravite,
            critere_stade=pred.critere_stade,
            critere_dar=pred.critere_dar,
            image_url=f"{base_url}/disease/image/{pred.file_path}"
        )


@router.get("/image/{path_id}", response_class=FileResponse)
async def get_plant_image(path_id: str):
    image_path = f"storage/plants/{path_id}"
    if not Path(image_path).exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)


@router.get("/image-predictions/")
async def get_image_predictions(
    request: Request,
    db: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user)

):
    predictions = db.query(ImagePrediction).filter(ImagePrediction.user_id == user.id).all()
    return [ImagePredictionOutput.from_orm_custom(p, request) for p in predictions]


