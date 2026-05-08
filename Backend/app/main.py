from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
from dotenv import load_dotenv
from pydantic import BaseModel # Para validar el cuerpo del login

# Buscamos el .env subiendo dos niveles
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)

app = FastAPI(title="Cybersecurity Tutor API")

# --- Modelos de Datos ---
from app.models.schemas import ChatRequest

class LoginRequest(BaseModel):
    nombre: str
    password: str

# --- Importamos Servicios ---
from app.services.agent import get_tutor_response
from app.services.analyzer import analyze_pcap
from app.services.auth_service import validar_credenciales # El servicio que creamos

# Configuración de CORS
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

# Directorio temporal para capturas
CAPTURES_DIR = "data/captures"
os.makedirs(CAPTURES_DIR, exist_ok=True)

@app.get("/")
def read_root():
    return {"message": "Tutor de Ciberseguridad Activo"}

# --- Endpoint de Autenticación (Migrado desde LoginModal.jsx) ---
@app.post("/api/login")
async def login_endpoint(credentials: LoginRequest):
    """Lógica de login que antes estaba en el Frontend"""
    user = validar_credenciales(credentials.nombre, credentials.password)
    
    if not user:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    
    return {"status": "success", "user": user}

# --- Endpoints de Tutoría y Análisis ---
@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        response = get_tutor_response(request.message)
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    file_path = os.path.join(CAPTURES_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        pcap_data = analyze_pcap(file_path)
        
        if isinstance(pcap_data, str) and "Error" in pcap_data:
            return {"status": "error", "message": pcap_data}
            
        user_msg = f"He subido el archivo {file.filename}. ¿Qué ataques o anomalías detectas?"
        narrative = get_tutor_response(user_msg, pcap_data=pcap_data)
        
        return {
            "status": "success",
            "narrative": narrative,
            "technical_details": pcap_data
        }
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)