from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from DB.database import Base
from typing import List, Optional

from passlib.handlers.bcrypt import bcrypt
from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Text

from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from DB.database import Base
from datetime import datetime, timezone

class IrrigationRecord(Base):
    __tablename__ = "irrigation_records"

    id = Column(Integer, primary_key=True, index=True)
    culture = Column(String, index=True)
    type_sol = Column(String)
    saison = Column(String)
    type_irrigation = Column(String)
    frequence_irrigation = Column(Integer)
    besoin_brut = Column(Float)
    besoin_par_seance = Column(Float)
    irrigation_necessaire = Column(Boolean)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = Column(Integer, ForeignKey("utilisateurs.id"))
    user = relationship("UserDB")

class UserDB(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    prenom = Column(String, nullable=False)
    adresse = Column(String, nullable=False)
    tel = Column(String(20), nullable=False)  # changer en String pour supporter les numéros avec + ou 0...
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    image = Column(String, nullable=True)

class CropRecommendation(Base):
    __tablename__ = "crop_recommendations"

    id = Column(Integer, primary_key=True, index=True)
    N = Column(Float)
    P = Column(Float)
    K = Column(Float)
    temperature = Column(Float)
    humidity = Column(Float)
    ph = Column(Float)
    rainfall = Column(Float)
    recommended_crop = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = Column(Integer, ForeignKey('utilisateurs.id'))
    user = relationship("UserDB")
    #pour la recommandation des matieres actives
    plant = Column(String, nullable=True)  # Apple
    disease = Column(String, nullable=True)  # Apple scab
    recommended_matiere = Column(String, nullable=True)

    critere_gravite = Column(String, nullable=True)
    critere_stade = Column(String, nullable=True)
    critere_dar = Column(String, nullable=True)

class ImagePrediction(Base):
    __tablename__ = "image_predictions"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    prediction = Column(String)
    file_path = Column(String)  # New field for storing file path
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = Column(Integer, ForeignKey('utilisateurs.id'))
    user = relationship("UserDB")

    # Champs supplémentaires requis pour la recommandation
    plant = Column(String, nullable=True)
    disease = Column(String, nullable=True)
    recommended_matiere = Column(String, nullable=True)
    critere_gravite = Column(String, nullable=True)
    critere_stade = Column(String, nullable=True)
    critere_dar = Column(String, nullable=True)

class ChatbotInteraction(Base):
    __tablename__ = "chatbot_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False)
    input_type = Column(String)  # "text" ou "audio"
    user_input = Column(String)  # texte saisi ou reconnu
    bot_response = Column(String)  # réponse de Gemini
    audio_filename = Column(String, nullable=True)  # si réponse audio
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("UserDB")

class ParcelleNote(Base):
    __tablename__ = "parcelle_notes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('utilisateurs.id'), nullable=False) # lien vers utilisateur

    image_url = Column(String, nullable=True)
    nom_ferme = Column(String, nullable=False)
    numero_parcelle = Column(String, nullable=False)
    superficie = Column(Float, nullable=False)
    type_sol = Column(String, nullable=False)
    culture = Column(String, nullable=False)
    date_semis = Column(String, nullable=False)
    quantite_semence = Column(Float, nullable=False)
    systeme_irrigation = Column(String, nullable=False)
    suivi_culture = Column(Text, nullable=False)
    date_recolte = Column(String, nullable=False)
    nombre_travailleurs = Column(Integer, nullable=False)
    depenses = Column(Float, nullable=False)
    rendement = Column(Float, nullable=False)
    autres_infos = Column(Text, nullable=True)
    date_creation = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    user = relationship("UserDB")
class ParcelleNoteFormattedResponse(BaseModel):
    id: int
    image_url: Optional[str]
    nom_ferme: str
    numero_parcelle: str
    superficie: str
    type_sol: str
    culture: str
    date_semis: str
    quantite_semence: str
    systeme_irrigation: str
    suivi_culture: str
    date_recolte: str
    nombre_travailleurs: str
    depenses: float
    rendement: str
    autres_infos: Optional[str]
    date_creation: datetime

    class Config:
        orm_mode = True
def format_parcelle(parcelle: ParcelleNote) -> ParcelleNoteFormattedResponse:
    return ParcelleNoteFormattedResponse(
        id=parcelle.id,
        image_url=parcelle.image_url,
        nom_ferme=parcelle.nom_ferme,
        numero_parcelle=parcelle.numero_parcelle,
        superficie=f"{parcelle.superficie} hectares",
        type_sol=parcelle.type_sol,
        culture=parcelle.culture,
        date_semis=parcelle.date_semis,
        quantite_semence=f"{parcelle.quantite_semence} kg/hectare",
        systeme_irrigation=parcelle.systeme_irrigation,
        suivi_culture=parcelle.suivi_culture,
        date_recolte=parcelle.date_recolte,
        nombre_travailleurs=f"{parcelle.nombre_travailleurs} personnes",
        depenses=parcelle.depenses,
        rendement=f"{parcelle.rendement} tonnes/hectare",
        autres_infos=parcelle.autres_infos,
        date_creation=parcelle.date_creation
    )
