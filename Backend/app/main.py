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

# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# --- Configuración de Rutas y Entorno ---
BASE_DIR = Path(__file__).resolve().parents[2]  # Backend/
load_dotenv(BASE_DIR / ".env")

# --- Importaciones de Servicios y Modelos ---
from app.scripts.ingest import run_ingestion
from app.models.schemas import ChatRequest
from app.services.agent import get_tutor_response, init_rag_service, get_pcap_analysis_response
from app.services.analyzer import analyze_pcap
from app.services.auth_service import validar_credenciales, registrar_usuario
# NUEVO: Lógica de persistencia y carga de historial
from app.services.chat_service import obtener_o_crear_sesion, guardar_mensaje_db, cargar_historial_db

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
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
    "http://localhost:5175",
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

# ==============================================================
# ENDPOINTS DE ESTADO Y AUTENTICACIÓN
# ==============================================================

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
# ENDPOINTS DE TUTORÍA (IA) Y PERSISTENCIA
# ==============================================================

@app.get("/api/chat/history/{email}")
async def get_chat_history(email: str):
    """
    Nuevo: Recupera el historial de chat de Supabase para un usuario.
    Evita el error 404 cuando el frontend carga el componente.
    """
    try:
        id_sesion = obtener_o_crear_sesion(email)
        historial = cargar_historial_db(id_sesion)
        return {"status": "success", "history": historial}
    except Exception as e:
        # Si no hay usuario o sesión aún, devolvemos historial vacío en lugar de error
        return {"status": "success", "history": []}

@app.delete("/api/chat/history/{email}")
async def delete_chat_history(email: str, nodo_actual: str = "inicio"):
    try:
        from app.services.chat_service import borrar_historial_db
        id_sesion = obtener_o_crear_sesion(email)
        exito = borrar_historial_db(id_sesion, nodo_actual)
        if exito:
            return {"status": "success", "message": "Historial borrado"}
        else:
            raise HTTPException(status_code=500, detail="Error al borrar historial en DB")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    if not app_state["is_ready"]:
        raise HTTPException(status_code=503, detail="La IA aún se está cargando.")
    
    try:
        # 1. Obtener sesión vinculada al ID real del usuario
        id_sesion = obtener_o_crear_sesion(request.email)

        # 2. Guardar mensaje del Estudiante
        guardar_mensaje_db(id_sesion, "user", request.message, request.nodo_actual)

        # 2.5 Cargar historial del nodo actual
        historial_db = cargar_historial_db(id_sesion)
        historial_nodo = [{"role": m["role"], "content": m["content"]} for m in historial_db if m["nodo"] == request.nodo_actual]

        # 3. Generar respuesta de la IA (RAG) con contexto del historial
        response = get_tutor_response(request.message, history=historial_nodo)

        # 4. Guardar respuesta del Tutor
        guardar_mensaje_db(id_sesion, "assistant", response, request.nodo_actual)

        return {"status": "success", "response": response}
    except Exception as e:
        print(f"Error en chat_endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_endpoint(email: str, file: UploadFile = File(...), nodo_actual: str = "analisis_pcap"):
    if not app_state["is_ready"]:
        raise HTTPException(status_code=503, detail="Sistema en inicialización.")

    file_path = CAPTURES_DIR / file.filename
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Análisis técnico con Scapy
        pcap_data = analyze_pcap(str(file_path))
        if isinstance(pcap_data, str) and "Error" in pcap_data:
            return {"status": "error", "message": pcap_data}

        # Persistencia del análisis en el historial
        id_sesion = obtener_o_crear_sesion(email)
        user_msg = f"Archivo analizado: {file.filename}"
        guardar_mensaje_db(id_sesion, "user", user_msg, nodo_actual)

        # Generar narrativa pedagógica sobre el tráfico
        narrative = get_pcap_analysis_response(pcap_data)
        
        guardar_mensaje_db(id_sesion, "assistant", narrative, nodo_actual)

        return {
            "status": "success",
            "narrative": narrative,
            "technical_details": pcap_data,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if file_path.exists():
            file_path.unlink()