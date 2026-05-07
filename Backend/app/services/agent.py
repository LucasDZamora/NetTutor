import os
from groq import Groq
from app.services.rag_service import RAGService

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
rag = RAGService()

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
- Si detectas un ataque, explica el "por qué" técnico (ej: el handshake TCP incompleto).
- Siempre termina con 3 opciones numeradas de "Siguientes Pasos".
"""

def get_tutor_response(user_message: str, pcap_data: dict = None):
    # 1. Identificar Tópico (Sustitución de Dialogflow)
    intent_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile", # O tu modelo de 120B preferido
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT_INTENT},
            {"role": "user", "content": user_message}
        ]
    )
    topic = intent_response.choices[0].message.content.strip().lower()

    # 2. Obtener contexto del RAG basado en el tópico y mensaje
    rag_context = rag.get_knowledge(user_message, topic=topic)

    # 3. Construir Prompt Final con datos de Scapy y RAG
    pcap_context = f"Datos de Scapy: {pcap_data}" if pcap_data else "No hay archivo subido aún."
    
    full_prompt = f"""
    CONTEXTO TÉCNICO (RAG):
    {rag_context}

    DATOS DE LA CAPTURA (SCAPY):
    {pcap_context}

    MENSAJE DEL USUARIO:
    {user_message}
    """

    try:
        final_response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT_TUTOR},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2 # Baja temperatura para respuestas más técnicas y precisas
        )
    except Exception as e:
        raise RuntimeError(f"Intent classification failed: {e}")

    if not final_response.choices:
        raise RuntimeError("No choices returned from intent model")

    return final_response.choices[0].message.content