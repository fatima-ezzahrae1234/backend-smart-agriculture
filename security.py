from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from config import env
from fastapi import HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from DB.database import get_session
from DB.models import UserDB
import re
from fastapi import HTTPException
from typing import Optional


SECRET_KEY = env("JWT_SECRET", "super-secret-key")
ALGORITHM = env("JWT_ALGORITHM", "HS256")

expire_days = int(env("JWT_DAYS", 31))
ACCESS_TOKEN_EXPIRE_MINUTES = expire_days * 24 * 60
# Contexte de hachage pour sécuriser les mots de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2PasswordBearer pour Swagger + récupération token dans les requêtes
oauth2_scheme = HTTPBearer()

# Fonction pour hacher un mot de passe
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Fonction pour vérifier un mot de passe (comparaison avec celui stocké)
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Fonction pour créer un token JWT
def create_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})  # issued at

    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Fonction pour décoder et valider un JWT
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise JWTError("Token invalide ou expiré") from e

# Fonction dépendance pour récupérer l'utilisateur connecté via token JWT
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(oauth2_scheme),
    db: Session = Depends(get_session)
) -> UserDB:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")

        user = db.query(UserDB).filter(UserDB.email == email).first()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé")

        return user

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide")


def validate_tel(tel: str):
    """
    Valide un numéro de téléphone marocain :
    - Peut commencer par +212 ou 0
    - Doit être suivi de 9 chiffres
    - Exemple valides : +212612345678, 0612345678
    """
    pattern = re.compile(r"^(?:\+212|0)([5-7]\d{8})$")
    if not pattern.match(tel):
        raise HTTPException(
            status_code=400,
            detail="Numéro de téléphone marocain invalide. Exemple : +212612345678 ou 0612345678"
        )
