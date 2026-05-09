import os
import re
from groq import Groq

from app.services.rag_service import RAGService

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

rag = None

ALLOWED_TOPICS = {
    "port_scan",
    "telnet",
    "pop3",
    "malware_c2",
    "dos",
    "http_phishing",
    "general",
}

SYSTEM_PROMPT_INTENT = """
Eres un clasificador de intenciones experto en ciberseguridad.
Tu tarea es analizar la consulta del usuario y determinar cuál de los 5 niveles de ataque está involucrado.
Responde ÚNICAMENTE con el nombre del tópico:
'port_scan', 'telnet', 'pop3', 'malware_c2', 'dos', 'http_phishing', o 'general'.
"""

SYSTEM_PROMPT_TUTOR = """
Eres un Tutor Proactivo de Ciberseguridad. Tu misión es guiar al estudiante usando el método socrático y técnico.
Cuentas con dos fuentes de verdad:
1. INFORMACIÓN DEL PCAP: Datos crudos extraídos de la captura subida.
2. CONTEXTO TÉCNICO RAG: Documentación oficial (RFCs, MITRE, OWASP).

REGLAS:
- No alucines. Si el RAG no menciona un detalle, usa tus conocimientos generales pero aclara que es teoría.
- Si detectas un ataque, explica el "por qué" técnico.
- Siempre termina con 3 opciones numeradas de "Siguientes Pasos".
"""


def init_rag_service():
    global rag
    if rag is None:
        rag = RAGService()
    return rag


def normalize_topic(raw: str) -> str:
    if not raw:
        return "general"

    txt = raw.strip().lower()
    txt = re.sub(r"[^a-z_]", "", txt)

    if txt in ALLOWED_TOPICS:
        return txt

    for topic in ALLOWED_TOPICS:
        if topic != "general" and topic in txt:
            return topic

    return "general"


def get_tutor_response(user_message: str, pcap_data: dict = None):
    global rag

    if rag is None:
        raise RuntimeError("RAG no inicializado todavía")

    intent_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_INTENT},
            {"role": "user", "content": user_message},
        ],
        temperature=0.0,
    )

    raw_topic = intent_response.choices[0].message.content.strip()
    topic = normalize_topic(raw_topic)

    rag_context = rag.get_knowledge(user_message, topic=topic)

    print(f"--- DEBUG RAG (RAW: {raw_topic!r} | TOPIC: {topic}) ---")
    print(rag_context if rag_context else "⚠️ RAG VACÍO - NO SE ENCONTRÓ NADA")
    print("-----------------------------------")

    pcap_context = f"Datos de Scapy: {pcap_data}" if pcap_data else "No hay archivo subido aún."

    full_prompt = f"""
CONTEXTO TÉCNICO (RAG):
{rag_context if rag_context else "No se recuperó contexto técnico adicional."}

DATOS DE LA CAPTURA (SCAPY):
{pcap_context}

MENSAJE DEL USUARIO:
{user_message}
"""

    final_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_TUTOR},
            {"role": "user", "content": full_prompt},
        ],
        temperature=0.2,
    )

    return final_response.choices[0].message.content