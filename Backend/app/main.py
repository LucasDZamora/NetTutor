from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Buscamos el .env subiendo dos niveles: de 'app' a 'backend' y de 'backend' a la raíz
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
load_dotenv(dotenv_path=dotenv_path)
app = FastAPI(title="Cybersecurity Tutor API")
import shutil

# Importamos los modelos y servicios
from app.models.schemas import ChatRequest
from app.services.agent import get_tutor_response
from app.services.analyzer import analyze_pcap


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

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """Endpoint para consultas de texto puro (RAG)"""
    try:
        response = get_tutor_response(request.message)
        return {"status": "success", "response": response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
async def analyze_endpoint(file: UploadFile = File(...)):
    """Endpoint para subir PCAP, analizar con Scapy y generar tutoría con RAG"""
    file_path = os.path.join(CAPTURES_DIR, file.filename)
    
    try:
        # 1. Guardar archivo
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Analizar con Scapy
        pcap_data = analyze_pcap(file_path)
        
        if isinstance(pcap_data, str) and "Error" in pcap_data:
            return {"status": "error", "message": pcap_data}
            
        # 3. Generar respuesta del tutor combinando Scapy + RAG
        # Usamos un mensaje inicial para disparar la narrativa del archivo
        user_msg = f"He subido el archivo {file.filename}. ¿Qué ataques o anomalías detectas?"
        narrative = get_tutor_response(user_msg, pcap_data=pcap_data)
        
        return {
            "status": "success",
            "narrative": narrative,
            "technical_details": pcap_data
        }
    finally:
        # Limpieza: eliminar el archivo después del análisis si no se desea persistir
        if os.path.exists(file_path):
            os.remove(file_path)