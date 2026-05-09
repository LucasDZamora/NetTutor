import os
# ==============================================================
# FIX ANTI-CONGELAMIENTO (DEADLOCK) PARA HUGGINGFACE EN HILOS
# ==============================================================
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import shutil
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from pydantic import BaseModel

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- Configuración de Rutas y Entorno ---
BASE_DIR = Path(__file__).resolve().parents[2]  # Backend/
load_dotenv(BASE_DIR / ".env")

# --- Importaciones de Servicios y Modelos ---
from app.scripts.ingest import run_ingestion
from app.models.schemas import ChatRequest
from app.services.agent import get_tutor_response, init_rag_service
from app.services.analyzer import analyze_pcap
from app.services.auth_service import validar_credenciales, registrar_usuario

# --- Esquemas para Autenticación ---
class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    nombre: str
    email: str
    password: str

# --- Gestión de Estado de la Aplicación ---
app_state = {
    "is_ready": False,
    "init_error": None,
    "phase": "starting",
}

def background_initialization():
    """Carga los documentos y la IA en un hilo separado para no bloquear la API"""
    try:
        app_state["phase"] = "ingesting"
        print("🛠️ Iniciando ingesta de documentos...")
        run_ingestion()
        
        app_state["phase"] = "loading_rag"
        print("🧠 Cargando modelos RAG en memoria...")
        init_rag_service()
        
        app_state["is_ready"] = True
        app_state["phase"] = "ready"
        print("🚀 TUTOR LISTO: Base de conocimientos y modelos cargados.")
    except Exception as e:
        app_state["init_error"] = str(e)
        app_state["phase"] = "error"
        print(f"❌ Error crítico en inicialización: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicia la carga pesada al arrancar
    thread = threading.Thread(target=background_initialization, daemon=True)
    thread.start()
    yield
    print("Cerrando servidor...")

app = FastAPI(title="Cybersecurity Tutor API", lifespan=lifespan)

# --- Configuración de CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CAPTURES_DIR = BASE_DIR / "data" / "captures"
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

# ==============================================================
# ENDPOINTS DE ESTADO Y AUTENTICACIÓN
# ==============================================================

@app.get("/")
def read_root():
    return {"message": "Tutor de Ciberseguridad Activo"}

@app.get("/api/status")
async def get_status():
    """Permite al Frontend saber si debe bloquear o no el chat"""
    return {
        "status": "ready" if app_state["is_ready"] else "initializing",
        "phase": app_state["phase"],
        "message": "Chat listo" if app_state["is_ready"] else "Inicializando base de conocimientos técnica...",
        "error": app_state["init_error"],
    }

@app.post("/api/login")
async def login_endpoint(credentials: LoginRequest):
    user = validar_credenciales(credentials.email, credentials.password)
    if not user:
        raise HTTPException(status_code=401, detail="Correo o contraseña incorrectos")
    return {"status": "success", "user": user}

@app.post("/api/register")
async def register_endpoint(user_data: RegisterRequest):
    nuevo_usuario = registrar_usuario(
        user_data.nombre, 
        user_data.email, 
        user_data.password
    )
    if not nuevo_usuario:
        raise HTTPException(status_code=400, detail="El correo ya existe o hubo un error")
    return {"status": "success", "message": "Usuario creado correctamente"}

# ==============================================================
# ENDPOINTS DE TUTORÍA (IA)
# ==============================================================

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not app_state["is_ready"]:
        raise HTTPException(status_code=503, detail="La IA aún se está cargando.")
    
    try:
        response = get_tutor_response(request.message)
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    if not app_state["is_ready"]:
        raise HTTPException(status_code=503, detail="Sistema en inicialización.")

    file_path = CAPTURES_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        pcap_data = analyze_pcap(str(file_path))
        if isinstance(pcap_data, str) and "Error" in pcap_data:
            return {"status": "error", "message": pcap_data}

        user_msg = f"He subido el archivo {file.filename}. ¿Qué ataques o anomalías detectas?"
        narrative = get_tutor_response(user_msg, pcap_data=pcap_data)

        return {
            "status": "success",
            "narrative": narrative,
            "technical_details": pcap_data,
        }
    finally:
        if file_path.exists():
            file_path.unlink()