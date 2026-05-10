import os
import re
import json
# pyrefly: ignore [missing-import]
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

# --- NUEVO PROMPT PARA DISEÑO DE ESCENARIOS ---
SYSTEM_PROMPT_SCENARIO_DESIGNER = """
Eres el Arquitecto de Simulaciones de NetTutor. Tu función es generar escenarios de ciberseguridad dinámicos y realistas basados en documentación técnica y un nivel de dificultad.

CONTEXTO TÉCNICO RECUPERADO DEL RAG (Usa esto para los detalles de los paquetes):
{contexto_rag}

REGLAS DE DISEÑO:
- VARIEDAD: Crea una situación ficticia diferente cada vez. No repitas nombres de empresas.
- REALISMO TÉCNICO: Utiliza el contexto RAG para definir IPs, puertos y protocolos correctos.
- GENERACIÓN DE TRÁFICO: Debes inventar una lista de al menos 20 paquetes que representen el ataque mencionado.
- FORMATO: Responde ÚNICAMENTE en formato JSON.

FORMATO DE SALIDA (JSON):
{{
  "escenario": {{
    "empresa_ficticia": "Nombre de la empresa",
    "descripcion_entorno": "Contexto del analista",
    "incidente_reportado": "Anomalía detectada",
    "objetivo_aprendizaje": "Lo que el estudiante debe descubrir"
  }},
  "guia_tutor": {{
    "mensaje_inicial": "Saludo inicial del tutor",
    "pistas_sistema": ["Pista 1", "Pista 2", "Pista 3"]
  }},
  "paquetes_pcap": [
    {{
      "no": 1,
      "time": "0.0000",
      "src": "IP_ORIGEN",
      "dst": "IP_DESTINO",
      "pr": "PROTOCOLO",
      "len": "LONGITUD",
      "info": "Descripción técnica (ej: [SYN], USER admin, etc.)"
    }}
  ],
  "metadata_simulacion": {{
    "dificultad": "Nivel {nivel_id}",
    "topico": "{topico}"
  }}
}}
"""

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

SYSTEM_PROMPT_PCAP_ANALYSIS = """
Actúa como un Tutor Proactivo de Ciberseguridad. Tu objetivo no es solo resumir, sino DIRIGIR el aprendizaje del usuario basándote en este archivo .pcap:

RESUMEN TÉCNICO DE SCAPY:
{pcap_summary}

INSTRUCCIONES DE FLUJO (Bifurcaciones Lógicas):
Analiza los datos y toma decisiones basadas en estas reglas:

1. BIFURCACIÓN DE SEGURIDAD:
   - SI detectas protocolos sin cifrar (HTTP, FTP, Telnet) o mDNS exponiendo nombres, inicia con una ALERTA proactiva.
   - SI todo es HTTPS/TLS, felicita al usuario por tener tráfico cifrado y explica por qué es importante.

2. BIFURCACIÓN DE PROTOCOLO:
   - SI hay handshakes TCP, elige un flujo y explica el proceso SYN-ACK.
   - SI hay mucho tráfico UDP/DNS, explica por qué este protocolo es "sin conexión".

3. BIFURCACIÓN DE IDENTIDAD:
   - SI ves IPs externas (Internet), identifica a qué servicio podrían pertenecer (Google, CDNs, etc.).
   - SI es solo tráfico local, explica la función del Router como Gateway.

FORMATO DE RESPUESTA (Estructura Directiva):
- Saludo de Tutor: "He analizado tu red y esto es lo que DEBES saber..."
- El Hallazgo Maestro: (Aplica las bifurcaciones arriba mencionadas).
- El "Por qué": Explica la lógica técnica detrás de tu conclusión.
- CIERRE DIRECTIVO: No esperes a que el usuario piense qué preguntar. Presenta 3 opciones numeradas de "Siguientes Pasos" (que representen nuevas intenciones de aprendizaje).

REGLA DE ORO: No seas pasivo. Tú eres el experto guiando a un novato.
"""

# --- NUEVA FUNCIÓN PARA GENERAR ESCENARIOS ---
def generate_scenario_data(nivel_id: int):
    """
    Genera un escenario dinámico basado en el nivel seleccionado, consultando el RAG.
    """
    global rag
    if rag is None:
        init_rag_service()
        
    topic_map = {
        1: "telnet",
        2: "http_phishing",
        3: "port_scan",
        4: "dos",
        5: "malware_c2"
    }
    topic = topic_map.get(nivel_id, "general")
    
    # 1. Obtener contexto real del RAG para alimentar al diseñador
    contexto_rag = rag.get_knowledge(f"Análisis y características técnicas de {topic}", topic=topic)
    
    # 2. Configurar el prompt
    prompt = SYSTEM_PROMPT_SCENARIO_DESIGNER.format(
        contexto_rag=contexto_rag if contexto_rag else "Información general sobre seguridad de red.",
        nivel_id=nivel_id,
        topico=topic
    )
    
    # 3. Llamada al LLM solicitando JSON
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.8, # Temperatura alta para asegurar escenarios diferentes cada vez
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)


def get_pcap_analysis_response(pcap_data: dict, history: list = None) -> str:
    prompt = SYSTEM_PROMPT_PCAP_ANALYSIS.format(pcap_summary=str(pcap_data))
    
    messages_to_send = [{"role": "system", "content": prompt}]
    
    if history:
        messages_to_send.extend(history)
    else:
        messages_to_send.append({"role": "user", "content": "Analiza los datos del PCAP y guía mi aprendizaje de acuerdo a las reglas establecidas."})
        
    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages_to_send,
        temperature=0.2,
    )
    return final_response.choices[0].message.content


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


def get_tutor_response(user_message: str, pcap_data: dict = None, history: list = None):
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

    pcap_context = f"Datos de Scapy: {pcap_data}" if pcap_data else "No hay archivo subido aún."

    full_system_prompt = f"""{SYSTEM_PROMPT_TUTOR}
CONTEXTO TÉCNICO (RAG):
{rag_context if rag_context else "No se recuperó contexto técnico adicional."}

DATOS DE LA CAPTURA (SCAPY):
{pcap_context}
"""

    messages_to_send = [{"role": "system", "content": full_system_prompt}]
    
    if history:
        messages_to_send.extend(history)
    else:
        messages_to_send.append({"role": "user", "content": user_message})

    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages_to_send,
        temperature=0.2,
    )

    return final_response.choices[0].message.content