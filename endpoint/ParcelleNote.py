from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional
import shutil
import os
import uuid

from DB.models import ParcelleNote, UserDB, format_parcelle, ParcelleNoteFormattedResponse
from DB.database import get_session
from security import get_current_user
from pydantic import BaseModel

router = APIRouter()


class ParcelleNoteResponse(BaseModel):
    id: int
    image_url: Optional[str]
    nom_ferme: str
    numero_parcelle: str
    superficie: float
    type_sol: str
    culture: str
    date_semis: str
    quantite_semence: float
    systeme_irrigation: str
    suivi_culture: str
    date_recolte: str
    nombre_travailleurs: int
    depenses: float
    rendement: float
    autres_infos: Optional[str]
    date_creation: datetime

    class Config:
        orm_mode = True


@router.post("/", response_model=ParcelleNoteResponse)
async def create_parcelle(
    image: UploadFile = File(None),
    nom_ferme: str = Form(...),
    numero_parcelle: str = Form(...),
    superficie: float = Form(...),
    type_sol: str = Form(...),
    culture: str = Form(...),
    date_semis: str = Form(...),
    quantite_semence: float = Form(...),
    systeme_irrigation: str = Form(...),
    suivi_culture: str = Form(...),
    date_recolte: str = Form(...),
    nombre_travailleurs: int = Form(...),
    depenses: float = Form(...),
    rendement: float = Form(...),
    autres_infos: Optional[str] = Form(None),
    session: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user),
):
    image_path = None
    if image:
        os.makedirs("storage/uploads", exist_ok=True)
        unique_filename = f"{uuid.uuid4().hex}_{image.filename}"
        image_path = f"storage/uploads/{unique_filename}"
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

    parcelle = ParcelleNote(
        user_id=user.id,
        image_url=image_path,
        nom_ferme=nom_ferme,
        numero_parcelle=numero_parcelle,
        superficie=superficie,
        type_sol=type_sol,
        culture=culture,
        date_semis=date_semis,
        quantite_semence=quantite_semence,
        systeme_irrigation=systeme_irrigation,
        suivi_culture=suivi_culture,
        date_recolte=date_recolte,
        nombre_travailleurs=nombre_travailleurs,
        depenses=depenses,
        rendement=rendement,
        autres_infos=autres_infos,
        date_creation=datetime.utcnow(),
    )
    session.add(parcelle)
    session.commit()
    session.refresh(parcelle)
    return parcelle


@router.get("/", response_model=List[ParcelleNoteFormattedResponse])
def read_parcelles(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    parcelles = db.query(ParcelleNote).filter(ParcelleNote.user_id == current_user.id).offset(skip).limit(limit).all()
    return [format_parcelle(p) for p in parcelles]


@router.get("/{parcelle_id}", response_model=ParcelleNoteFormattedResponse)
def read_parcelle(
    parcelle_id: int,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    parcelle = db.query(ParcelleNote).filter(
        ParcelleNote.id == parcelle_id,
        ParcelleNote.user_id == current_user.id
    ).first()

    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle non trouvée")

    return format_parcelle(parcelle)


@router.put("/{parcelle_id}", response_model=ParcelleNoteResponse)
def update_parcelle(
    parcelle_id: int,
    nom_ferme: str = Form(...),
    numero_parcelle: str = Form(...),
    superficie: float = Form(...),
    type_sol: str = Form(...),
    culture: str = Form(...),
    date_semis: str = Form(...),
    quantite_semence: float = Form(...),
    systeme_irrigation: str = Form(...),
    suivi_culture: str = Form(...),
    date_recolte: str = Form(...),
    nombre_travailleurs: int = Form(...),
    depenses: str = Form(...),  # <-- Accept as string
    rendement: float = Form(...),
    autres_infos: Optional[str] = Form(None),
    db: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user),
):
    parcelle = db.query(ParcelleNote).filter(
        ParcelleNote.id == parcelle_id,
        ParcelleNote.user_id == user.id
    ).first()

    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle non trouvée")

    # Safely parse 'depenses'
    try:
        depenses_clean = depenses.replace(",", "").replace(" ", "")
        depenses_value = float(depenses_clean)
    except ValueError:
        raise HTTPException(status_code=422, detail="Le format de 'dépenses' est invalide.")

    parcelle.nom_ferme = nom_ferme
    parcelle.numero_parcelle = numero_parcelle
    parcelle.superficie = superficie
    parcelle.type_sol = type_sol
    parcelle.culture = culture
    parcelle.date_semis = date_semis
    parcelle.quantite_semence = quantite_semence
    parcelle.systeme_irrigation = systeme_irrigation
    parcelle.suivi_culture = suivi_culture
    parcelle.date_recolte = date_recolte
    parcelle.nombre_travailleurs = nombre_travailleurs
    parcelle.depenses = depenses_value
    parcelle.rendement = rendement
    parcelle.autres_infos = autres_infos

    db.commit()
    db.refresh(parcelle)
    return parcelle



@router.delete("/{parcelle_id}")
def delete_parcelle(
    parcelle_id: int,
    db: Session = Depends(get_session),
    current_user=Depends(get_current_user),
):
    parcelle = db.query(ParcelleNote).filter(
        ParcelleNote.id == parcelle_id,
        ParcelleNote.user_id == current_user.id
    ).first()

    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle non trouvée")

    db.delete(parcelle)
    db.commit()
    return {"detail": "Parcelle supprimée"}
