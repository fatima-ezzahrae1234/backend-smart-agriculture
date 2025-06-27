from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
import json
import os

from DB.database import get_session
from security import get_current_user
from DB.models import UserDB

router = APIRouter()

# Emplacement du fichier JSON
CHEMIN_JSON = "storage/catalogue_complet.json"

@router.get("/catalogue/{nom_catalogue}")
def lire_catalogue(
    nom_catalogue: str,
    db: Session = Depends(get_session),
    user: UserDB = Depends(get_current_user)  # Authentification sécurisée
):
    if not os.path.exists(CHEMIN_JSON):
        raise HTTPException(status_code=500, detail="Fichier catalogue non trouvé")

    try:
        with open(CHEMIN_JSON, "r", encoding="utf-8") as fichier:
            data = json.load(fichier)

        for catalogue in data:
            if catalogue["catalogue"].lower() == nom_catalogue.lower():
                return {
                    "catalogue": catalogue["catalogue"],
                    "liens_sites": catalogue.get("liens_sites", []),
                    "produits": catalogue.get("produits", [])
                }

        raise HTTPException(status_code=404, detail="Catalogue introuvable")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))