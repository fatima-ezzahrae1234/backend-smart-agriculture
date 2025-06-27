
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import Optional
import os
import imghdr
import re
from DB.database import get_session
from DB.models import UserDB
from security import hash_password, verify_password, create_token, get_current_user

router = APIRouter()

# Validation téléphone marocain
def validate_tel(tel: str) -> str:
    pattern = r"^0[5-7][0-9]{8}$"
    if not re.fullmatch(pattern, tel):
        raise HTTPException(status_code=400, detail="Numéro de téléphone marocain invalide. Format attendu : 0XXXXXXXXX")
    return tel

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    nom: str = Form(...),
    prenom: str = Form(...),
    adresse: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    tel: str = Form(...),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_session)
):
    # Validation téléphone
    validate_tel(tel)

    # Vérifier si email existe déjà
    if db.query(UserDB).filter(UserDB.email == email).first():
        raise HTTPException(status_code=400, detail="Email déjà utilisé")

    # Hasher le mot de passe
    hashed_pw = hash_password(password)

    # Gérer upload image
    image_path = None
    if image:
        image_bytes = await image.read()
        image_type = imghdr.what(None, h=image_bytes)
        if image_type not in ("jpeg", "png", "gif", "bmp"):
            raise HTTPException(status_code=400, detail="Format d'image non supporté")

        image_folder = "user_images"
        os.makedirs(image_folder, exist_ok=True)

        _, ext = os.path.splitext(image.filename)
        ext = ext.lower()
        safe_email = email.replace("@", "_at_").replace(".", "_dot_")
        safe_filename = f"{safe_email}{ext}"

        image_path = os.path.join(image_folder, safe_filename)

        with open(image_path, "wb") as f:
            f.write(image_bytes)

    # Créer utilisateur en DB
    new_user = UserDB(
        nom=nom,
        prenom=prenom,
        adresse=adresse,
        email=email,
        tel=tel,
        hashed_password=hashed_pw,
        image=image_path
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"message": "Utilisateur inscrit avec succès"})

@router.post("/login")
async def login(
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_session)
):
    user = db.query(UserDB).filter(UserDB.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants incorrects")

    token = create_token({"sub": user.email})

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "nom": user.nom,
            "prenom": user.prenom,
            "adresse": user.adresse,
            "email": user.email,
            "tel": user.tel,
            "image": user.image
        }
    }

# Récupérer l'utilisateur connecté via token JWT
@router.get("/me")
def get_me(current_user: UserDB = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "nom": current_user.nom,
        "prenom": current_user.prenom,
        "adresse": current_user.adresse,
        "email": current_user.email,
        "tel": current_user.tel,
        "image": current_user.image
    }
@router.put("/update-profile")
async def update_profile(
    nom: Optional[str] = Form(None),
    prenom: Optional[str] = Form(None),
    adresse: Optional[str] = Form(None),
    tel: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_session),
    current_user: UserDB = Depends(get_current_user)
):
    if tel:
        validate_tel(tel)

    if nom:
        current_user.nom = nom
    if prenom:
        current_user.prenom = prenom
    if adresse:
        current_user.adresse = adresse
    if tel:
        current_user.tel = tel

    # Modifier mot de passe
    if password:
        current_user.hashed_password = hash_password(password)

    # Modifier l'image
    if image:
        image_bytes = await image.read()
        image_type = imghdr.what(None, h=image_bytes)
        if image_type not in ("jpeg", "png", "gif", "bmp"):
            raise HTTPException(status_code=400, detail="Format d'image non supporté")

        image_folder = "user_images"
        os.makedirs(image_folder, exist_ok=True)
        _, ext = os.path.splitext(image.filename)
        ext = ext.lower()
        safe_email = current_user.email.replace("@", "_at_").replace(".", "_dot_")
        safe_filename = f"{safe_email}{ext}"
        image_path = os.path.join(image_folder, safe_filename)

        with open(image_path, "wb") as f:
            f.write(image_bytes)

        current_user.image = image_path

    db.commit()
    db.refresh(current_user)

    return {
        "message": "Profil mis à jour avec succès",
        "user": {
            "id": current_user.id,
            "nom": current_user.nom,
            "prenom": current_user.prenom,
            "adresse": current_user.adresse,
            "email": current_user.email,
            "tel": current_user.tel,
            "image": current_user.image
        }
    }

@router.delete("/delete-account")
def delete_account(
    db: Session = Depends(get_session),
    current_user: UserDB = Depends(get_current_user)
):
    db.delete(current_user)
    db.commit()
    return {"message": "Compte supprimé avec succès"}
