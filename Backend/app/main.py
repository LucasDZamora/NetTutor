import os
# ==============================================================
# FIX ANTI-CONGELAMIENTO (DEADLOCK) PARA HUGGINGFACE EN HILOS
# ==============================================================
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import shutil
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parents[2]  # Backend/
load_dotenv(BASE_DIR / ".env")

from app.scripts.ingest import run_ingestion
from app.models.schemas import ChatRequest
from app.services.agent import get_tutor_response, init_rag_service
from app.services.analyzer import analyze_pcap

app_state = {
    "is_ready": False,
    "init_error": None,
    "phase": "starting",
}

ready_event = threading.Event()

def background_initialization():
    try:
        app_state["phase"] = "ingesting"
        print("🛠️ Iniciando ingesta...")
        
        # Ejecuta la ingesta si es necesario (el script ya chequea internamente o sobreescribe)
        run_ingestion()
        print("✅ Ingesta completada o verificada.")

        app_state["phase"] = "loading_rag"
        print("🧠 Cargando RAG en memoria...")
        init_rag_service()
        print("✅ RAG listo.")

        app_state["is_ready"] = True
        app_state["phase"] = "ready"
        ready_event.set()
        print("🚀 TUTOR LISTO PARA RECIBIR PREGUNTAS")

    except Exception as e:
        app_state["init_error"] = str(e)
        app_state["phase"] = "error"
        ready_event.set()
        print(f"❌ Error crítico en inicialización: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # El hilo secundario ahora es seguro gracias a TOKENIZERS_PARALLELISM = false
    thread = threading.Thread(target=background_initialization, daemon=True)
    thread.start()
    yield
    print("Cerrando servidor...")

app = FastAPI(title="Cybersecurity Tutor API", lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CAPTURES_DIR = BASE_DIR / "data" / "captures"
CAPTURES_DIR.mkdir(parents=True, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Tutor de Ciberseguridad Activo"}

@app.get("/api/status")
async def get_status():
    return {
        "status": "ready" if app_state["is_ready"] else "initializing",
        "phase": app_state["phase"],
        "message": "Chat listo" if app_state["is_ready"] else "Inicializando base de conocimientos técnica...",
        "error": app_state["init_error"],
    }

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not app_state["is_ready"]:
        raise HTTPException(
            status_code=503,
            detail=f"El tutor aún se está inicializando. Fase actual: {app_state['phase']}"
        )

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