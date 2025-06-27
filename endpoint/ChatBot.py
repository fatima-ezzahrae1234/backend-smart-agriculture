from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from google.generativeai import GenerativeModel, configure
from gtts import gTTS
import speech_recognition as sr
import uuid
import os
from pydub import AudioSegment
import io
from datetime import datetime
from sqlalchemy.orm import Session
from config import env
from DB.database import get_session
from DB.models import ChatbotInteraction, UserDB  # <-- assure-toi que ce modèle est bien dans DB.models
from security import get_current_user     # <-- pour récupérer l'utilisateur connecté

API_KEY = env("GEMINI_API_KEY")
configure(api_key=API_KEY)
model = GenerativeModel("gemini-1.5-flash")
from pydub import AudioSegment
from shutil import which
from pydub import AudioSegment

ffmpeg_path = which("ffmpeg")
if ffmpeg_path is None:
    print("⚠️ ffmpeg non trouvé - les routes audio ne fonctionneront pas")
else:
    AudioSegment.converter = ffmpeg_path


router = APIRouter()

AUDIO_FOLDER = os.path.abspath("audio_responses")
os.makedirs(AUDIO_FOLDER, exist_ok=True)


from fastapi import Request

@router.post("/chat/text")
async def chat_text(
    message: str = Form(None),
    lang: str = Form("ar"),
    db: Session = Depends(get_session),
    current_user: UserDB = Depends(get_current_user),
):
    print("📥 Reçu dans /chat/text:")
    print(f"message: {message}")
    print(f"lang: {lang}")
    print(f"user: {current_user.id if current_user else 'non authentifié'}")

    if not message:
        raise HTTPException(400, "Le champ 'message' est manquant ou vide.")

    try:
        print("📡 Appel de Gemini avec:", message)
        response = model.generate_content(message)
        print("✅ Réponse brute:", response)

        response_text = response.text
        print("📝 Réponse texte:", response_text)

        interaction = ChatbotInteraction(
            user_id=current_user.id,
            input_type="text",
            user_input=message,
            bot_response=response_text,
            audio_filename=None,
            timestamp=datetime.utcnow()
        )
        db.add(interaction)
        db.commit()

        return {"response": response_text}
    except Exception as e:
        print("💥 Exception attrapée:", str(e))
        raise HTTPException(500, f"Erreur: {str(e)}")




@router.post("/chat/audio")
async def chat_audio(
    file: UploadFile = File(...),
    lang: str = Form("ar"),
    db: Session = Depends(get_session),
    current_user: UserDB = Depends(get_current_user)
):
    try:
        file_content = await file.read()
        print(f"📥 Fichier reçu: {file.filename}, taille: {len(file_content)} octets")

        # ➕ Ajouter cette ligne pour détecter l’extension :
        extension = file.filename.split(".")[-1].lower()

        # ✅ Lire l’audio avec le bon format automatiquement
        audio = AudioSegment.from_file(io.BytesIO(file_content), format=extension)

        wav_path = f"temp_{uuid.uuid4()}.wav"
        audio.export(wav_path, format="wav")
    except Exception as e:
        raise HTTPException(400, f"Erreur conversion: {str(e)}")

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
        user_input = recognizer.recognize_google(audio_data, language=f"{lang}-{lang.upper()}")
    except Exception as e:
        os.remove(wav_path)
        raise HTTPException(400, f"Erreur reconnaissance: {str(e)}")

    os.remove(wav_path)

    try:
        response = model.generate_content(user_input)
        response_text = response.text

        audio_filename = f"response_{uuid.uuid4()}.mp3"
        audio_path = os.path.join(AUDIO_FOLDER, audio_filename)
        tts = gTTS(text=response_text, lang=lang)
        tts.save(audio_path)

        # Sauvegarde en base de données
        interaction = ChatbotInteraction(
            user_id=current_user.id,
            input_type="audio",
            user_input=user_input,
            bot_response=response_text,
            audio_filename=audio_filename,
            timestamp=datetime.utcnow()
        )
        db.add(interaction)
        db.commit()

        return {
            "text": response_text,
            "audio_url": f"/audio/{audio_filename}"
        }
    except Exception as e:
        raise HTTPException(500, f"Erreur génération: {str(e)}")


@router.get("/audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join(AUDIO_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(404, "Fichier non trouvé")
    return FileResponse(file_path, media_type="audio/mpeg")


@router.get("/debug/audio_folder")
async def debug_audio_folder():
    return {
        "path": AUDIO_FOLDER,
        "exists": os.path.exists(AUDIO_FOLDER),
        "files": os.listdir(AUDIO_FOLDER) if os.path.exists(AUDIO_FOLDER)else[]
}