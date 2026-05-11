import os
import re
import json
from typing import Any, Dict, List, Optional

# pyrefly: ignore [missing-import]
from groq import Groq

from app.services.rag_service import RAGService

client = Groq(api_key=os.getenv("GROQ_API_KEY"))
rag: Optional[RAGService] = None

ALLOWED_TOPICS = {
    "port_scan",
    "texto_plano",
    "pop3",
    "malware_c2",
    "dos",
    "http_phishing",
    "general",
}

LEVELS = {
    1: "texto_plano",
    2: "http_phishing",
    3: "port_scan",
    4: "dos",
    5: "malware_c2",
}

# =========================
# PROMPTS BASE
# =========================

SYSTEM_PROMPT_GENERAL_ROUTER = """
Eres el Router de Intenciones para el Chat General de NetTutor.
Tu tarea es analizar la consulta del usuario y clasificarla.

Debes responder SOLO en JSON válido.

ESQUEMA JSON OBLIGATORIO:
{
  "intent": "ask_concept|request_analysis|troubleshoot|general_chat",
  "topic": "port_scan|texto_plano|pop3|malware_c2|dos|http_phishing|general",
  "needs_rag": true,
  "summary": "Breve resumen de lo que el usuario quiere lograr"
}
"""

SYSTEM_PROMPT_GENERAL_TUTOR = """
Eres un Tutor Técnico Directivo en Ciberseguridad.
A diferencia de un bot de chat común, tu objetivo es dar respuestas DIRECTAS, CLARAS y RESOLUTIVAS, pero manteniendo en todo momento tu rol de TUTOR experto guiando a un estudiante.

Cuentas con:
1. INTENCIÓN DEL USUARIO: {intent_json}
2. INFORMACIÓN DEL PCAP: Datos de la captura subida.
3. CONTEXTO TÉCNICO RAG: Documentación técnica.

REGLAS:
- Ve directo al grano. Usa un tono profesional y resolutivo.
- Si el usuario pide un concepto, defínelo claramente.
- Si pide analizar el PCAP, dale el análisis directo sin preámbulos.
- NO uses el método socrático. Si el usuario se equivoca, simplemente dale la respuesta correcta.
- Al final de tu mensaje, SIEMPRE ofrece 2 o 3 opciones cortas y numeradas para que el usuario elija hacia dónde dirigir la conversación (ej. "1. Profundizar en X", "2. Analizar el tráfico Y").
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

SYSTEM_PROMPT_ROUTER = """
Eres el Router Cognitivo de NetTutor.

Tu tarea es analizar la intención del usuario, su avance dentro del simulador, el historial breve y la memoria resumida.
Debes decidir:
1) qué quiere hacer el usuario,
2) qué tan avanzado está,
3) a qué tópico pertenece,
4) si necesita RAG,
5) cuál es la siguiente bifurcación pedagógica.

Debes responder SOLO en JSON válido.

OBJETIVO:
- Ser flexible y más potente que un clasificador rígido.
- Detectar intención, subintención y progreso.
- Inferir referencia a paquetes, observaciones previas o conceptos implícitos.
- Actualizar memoria resumida sin repetir todo el historial.

REGLAS:
- Si el usuario usa pronombres como "este", "ese", "eso", "el anterior", "el que tiene SYN", usa el historial y la memoria para inferir a qué se refiere.
- Si no puedes inferir un paquete o evento concreto, deja packet_id en null.
- Si la consulta está fuera del simulador o fuera de los 5 niveles, marca topic = "general".
- No inventes datos técnicos.
- No expliques; solo clasifica y resume.
- No uses markdown.
- No agregues texto fuera del JSON.
- Si el usuario identifica o acierta la vulnerabilidad principal del escenario, debes marcar "completed": true en progress.

ESQUEMA JSON OBLIGATORIO:
{
  "intent": "identify_attack|describe_observation|ask_concept|request_mitigation|compare_protocols|confirm_understanding|advance_level|general",
  "branch": "novice|intermediate|advanced|unclear|off_topic",
  "topic": "port_scan|texto_plano|pop3|malware_c2|dos|http_phishing|general",
  "question_focus": "resumen corto de lo que realmente pregunta",
  "packet_id": 123,
  "needs_rag": true,
  "progress": {
    "level": 1,
    "stage": "start|diagnosis|explanation|mitigation|review",
    "completed": false
  },
  "memory_update": "resumen corto y útil de lo que cambió en esta interacción",
  "confidence": 0.0
}
"""

SYSTEM_PROMPT_SIM_TUTOR = """
Eres un Tutor Proactivo de Ciberseguridad en un chat interactivo.

Tu misión es responder usando:
1) la intención estructurada del router,
2) la memoria resumida,
3) el contexto del PCAP,
4) el contexto técnico recuperado del RAG.

REGLAS ABSOLUTAS:
1. RESPUESTAS CORTAS Y CONVERSACIONALES: Eres un tutor en un chat, NO un generador de reportes. Tus respuestas deben ser breves, directas y en lenguaje natural (ej. "No es correcto, deberías enfocarte en la columna de información."). NO uses encabezados (como "Hallazgo central", "Explicación técnica"), NO uses viñetas largas, y evita párrafos extensos.

2. CONDICIÓN DE VICTORIA: Si el JSON del router indica `"completed": true` (el usuario identificó la vulnerabilidad), tu respuesta DEBE COMENZAR EXACTAMENTE CON LA FRASE: "Encontraste la vulnerabilidad, nivel completado." y a continuación, en el mismo mensaje, explica brevemente cómo resolver o mitigar esta vulnerabilidad. ESTÁ ESTRICTAMENTE PROHIBIDO hacer nuevas preguntas o incluir la sección de "Siguientes pasos" en este caso.

3. EN CUALQUIER OTRO CASO: Guía al alumno paso a paso usando el método socrático de forma muy concisa. Termina tu mensaje con UNA sola pregunta corta o sugerencia puntual que invite al alumno a pensar o investigar el siguiente paso. NO des 3 opciones largas de siguientes pasos.

4. REGLA ANTI-SPOILERS: Mientras `"completed": false`, TIENES ESTRICTAMENTE PROHIBIDO mencionar o confirmar explícitamente el nombre del ataque o vulnerabilidad (ej. "phishing HTTP", "texto plano", "port scan", "DDOS", "malware"). Refiérete al problema como "anomalía", "tráfico sospechoso", "comportamiento inusual", etc. Deja que el estudiante lo deduzca y lo nombre.
"""

SYSTEM_PROMPT_SCENARIO_DESIGNER = """
Eres el Arquitecto de Simulaciones de NetTutor.

Genera escenarios de ciberseguridad realistas basados en el tópico, el nivel y el contexto técnico recuperado del RAG.

Debes producir SOLO JSON válido.

REGLAS ABSOLUTAS PARA EL PCAP:
1. REALISMO Y RUIDO DE FONDO: Un archivo PCAP real NUNCA tiene solo paquetes maliciosos. La gran mayoría del tráfico debe ser "ruido de fondo" normal y benigno (ej. peticiones ARP, consultas DNS a dominios comunes, tráfico TLS/HTTPS normal, handshakes TCP regulares, etc.).
2. CAMUFLAJE: La vulnerabilidad o ataque (definida por el tópico y el contexto del RAG) debe estar "escondida" y dispersa lógicamente entre el tráfico normal.
3. CANTIDAD: Debes generar EXACTAMENTE 30 paquetes en total. (La mayoría deben ser tráfico normal/benigno).
4. El escenario debe ser diferente cada vez y usar detalles técnicos coherentes con el contexto recuperado.
5. Usa direcciones IP de origen y destino variadas para simular una red real, pero mantén consistencia en la dirección IP de la víctima y el atacante durante el flujo malicioso.
6. La finalidad es entrenamiento pedagógico, no explotación real.
7. REGLA ANTI-SPOILERS: En `incidente_reportado`, `objetivo_aprendizaje`, `mensaje_inicial` y `pistas_sistema`, ESTÁ ESTRICTAMENTE PROHIBIDO mencionar el nombre de la vulnerabilidad o ataque (ej. no uses palabras como "texto plano", "DDOS", "phishing", "malware", "port scan"). Solo describe los SÍNTOMAS percibidos por los usuarios o el sistema (ej. "lentitud anómala", "acceso no autorizado reportado", "tráfico inusual de red"). El estudiante DEBE descubrir qué pasa.

ENTRADA:
- tópico
- nivel
- contexto técnico RAG

SALIDA JSON:
{
  "escenario": {
    "empresa_ficticia": "...",
    "descripcion_entorno": "...",
    "incidente_reportado": "...",
    "objetivo_aprendizaje": "..."
  },
  "guia_tutor": {
    "mensaje_inicial": "...",
    "pistas_sistema": ["...", "...", "..."]
  },
  "paquetes_pcap": [
    {
      "no": 1,
      "time": "0.0000",
      "src": "IP_ORIGEN",
      "dst": "IP_DESTINO",
      "pr": "PROTOCOLO",
      "len": "LONGITUD",
      "info": "..."
    }
  ],
  "metadata_simulacion": {
    "dificultad": "Nivel X",
    "topico": "..."
  }
}
"""

# =========================
# UTILIDADES
# =========================

def _clip_text(text: str, max_len: int = 2500) -> str:
    if not text:
        return ""
    if len(text) <= max_len:
        return text
    return text[:max_len] + "\n...[TRUNCADO]..."


def _pretty(obj: Any, max_len: int = 2500) -> str:
    try:
        if isinstance(obj, (dict, list)):
            txt = json.dumps(obj, ensure_ascii=False, indent=2)
        else:
            txt = str(obj)
        return _clip_text(txt, max_len=max_len)
    except Exception:
        return _clip_text(str(obj), max_len=max_len)


def init_rag_service():
    global rag
    if rag is None:
        rag = RAGService()
    return rag


def get_rag_service():
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


def safe_json_loads(text: str) -> Dict[str, Any]:
    if not text:
        return {}

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return {}

    return {}


def normalize_router_output(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        data = {}

    progress = data.get("progress", {})
    if not isinstance(progress, dict):
        progress = {}

    normalized = {
        "intent": data.get("intent", "general"),
        "branch": data.get("branch", "unclear"),
        "topic": normalize_topic(data.get("topic", "general")),
        "question_focus": str(data.get("question_focus", "")).strip(),
        "packet_id": data.get("packet_id", None),
        "needs_rag": bool(data.get("needs_rag", True)),
        "progress": {
            "level": int(progress.get("level", 0) or 0),
            "stage": progress.get("stage", "start"),
            "completed": bool(progress.get("completed", False)),
        },
        "memory_update": str(data.get("memory_update", "")).strip(),
        "confidence": float(data.get("confidence", 0.0) or 0.0),
    }

    pid = normalized["packet_id"]
    if pid in ("", "null", "None", None):
        normalized["packet_id"] = None
    else:
        try:
            normalized["packet_id"] = int(pid)
        except Exception:
            normalized["packet_id"] = None

    return normalized


def update_long_memory(memory_summary: str, router_json: Dict[str, Any]) -> str:
    current = (memory_summary or "").strip()
    update = router_json.get("memory_update", "").strip()

    if not update:
        return current

    if not current:
        return update

    merged = current + " | " + update
    return merged[-1200:]


def _log_llm1_input(user_message: str, history: Optional[List[Dict[str, str]]], memory_summary: str, pcap_data: Optional[Dict[str, Any]]):
    print("\n" + "=" * 80)
    print("LLM1 (ROUTER) - INPUT")
    print("-" * 80)
    print("USER MESSAGE:")
    print(_clip_text(user_message, 1500))
    print("\nMEMORY SUMMARY:")
    print(_clip_text(memory_summary or "vacía", 1500))
    print("\nHISTORY:")
    print(_pretty(history or [], 1500))
    print("\nPCAP DATA:")
    print(_pretty(pcap_data or {}, 1500))
    print("=" * 80 + "\n")


def _log_llm1_output(raw: str, parsed: Dict[str, Any]):
    print("\n" + "=" * 80)
    print("LLM1 (ROUTER) - RAW OUTPUT")
    print("-" * 80)
    print(_clip_text(raw, 2500))
    print("\nLLM1 (ROUTER) - PARSED JSON")
    print("-" * 80)
    print(_pretty(parsed, 2500))
    print("=" * 80 + "\n")


def _log_llm2_input(router_json: Dict[str, Any], rag_context: str, pcap_data: Optional[Dict[str, Any]], history: Optional[List[Dict[str, str]]], user_message: str, memory_summary: str):
    print("\n" + "=" * 80)
    print("LLM2 (TUTOR) - INPUT")
    print("-" * 80)
    print("ROUTER JSON:")
    print(_pretty(router_json, 2500))
    print("\nRAG CONTEXT:")
    print(_clip_text(rag_context or "vacío", 3500))
    print("\nMEMORY SUMMARY:")
    print(_clip_text(memory_summary or "vacía", 1500))
    print("\nPCAP DATA:")
    print(_pretty(pcap_data or {}, 1500))
    print("\nHISTORY:")
    print(_pretty(history or [], 1500))
    print("\nCURRENT USER MESSAGE:")
    print(_clip_text(user_message, 1500))
    print("=" * 80 + "\n")


def _log_llm2_output(raw: str):
    print("\n" + "=" * 80)
    print("LLM2 (TUTOR) - RAW OUTPUT")
    print("-" * 80)
    print(_clip_text(raw, 4000))
    print("=" * 80 + "\n")

# =========================
# ROUTER
# =========================

def route_intention(
    user_message: str,
    history: Optional[List[Dict[str, str]]] = None,
    memory_summary: str = "",
    pcap_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    history = history or []
    _log_llm1_input(user_message, history, memory_summary, pcap_data)

    pcap_context = f"PCAP: {json.dumps(pcap_data, ensure_ascii=False)}" if pcap_data else "PCAP: null"

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT_ROUTER,
        },
        {
            "role": "user",
            "content": f"""
MEMORIA RESUMIDA:
{memory_summary if memory_summary else "vacía"}

HISTORIAL BREVE:
{json.dumps(history, ensure_ascii=False)}

DATOS DE PCAP:
{pcap_context}

MENSAJE ACTUAL:
{user_message}

Devuelve SOLO JSON.
""".strip(),
        },
    ]

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages,
        temperature=0.1,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    parsed = safe_json_loads(raw)
    normalized = normalize_router_output(parsed)

    _log_llm1_output(raw, normalized)
    return normalized

# =========================
# TUTOR SIMULADOR
# =========================

def get_simulator_response(
    user_message: str,
    pcap_data: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    memory_summary: str = "",
):
    global rag

    if rag is None:
        raise RuntimeError("RAG no inicializado todavía")

    router_json = route_intention(
        user_message=user_message,
        history=history,
        memory_summary=memory_summary,
        pcap_data=pcap_data,
    )

    topic = router_json["topic"]
    intent = router_json["intent"]
    branch = router_json["branch"]
    level = router_json["progress"]["level"]
    stage = router_json["progress"]["stage"]

    rag_context = ""
    if router_json.get("needs_rag", True):
        rag_context = rag.get_knowledge(user_message, topic=topic)

    # recorte para evitar prompts gigantes
    rag_context = _clip_text(rag_context, 3000)

    pcap_context = f"Datos de Scapy: {pcap_data}" if pcap_data else "No hay archivo subido aún."

    full_system_prompt = f"""{SYSTEM_PROMPT_SIM_TUTOR}

JSON DEL ROUTER:
{json.dumps(router_json, ensure_ascii=False, indent=2)}

MEMORIA RESUMIDA:
{memory_summary if memory_summary else "vacía"}

CONTEXTO TÉCNICO (RAG):
{rag_context if rag_context else "No se recuperó contexto técnico adicional."}

DATOS DE LA CAPTURA (SCAPY):
{pcap_context}
"""

    messages_to_send = [{"role": "system", "content": full_system_prompt}]
    if history:
        messages_to_send.extend(history)
    messages_to_send.append({"role": "user", "content": user_message})

    _log_llm2_input(router_json, rag_context, pcap_data, history, user_message, memory_summary)

    final_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages_to_send,
        temperature=0.2,
    )

    answer = final_response.choices[0].message.content
    _log_llm2_output(answer)

    return {
        "response": answer,
        "router": router_json,
        "memory_next": update_long_memory(memory_summary, router_json),
        "meta": {
            "topic": topic,
            "intent": intent,
            "branch": branch,
            "level": level,
            "stage": stage,
        },
    }

# =========================
# CHAT GENERAL
# =========================

def get_tutor_response(
    user_message: str,
    pcap_data: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
):
    global rag

    if rag is None:
        raise RuntimeError("RAG no inicializado todavía")

    # 1. Router de intención con gpt-oss-120b
    router_messages = [
        {"role": "system", "content": SYSTEM_PROMPT_GENERAL_ROUTER},
        {"role": "user", "content": f"MENSAJE ACTUAL:\n{user_message}"}
    ]
    if history:
        historial_breve = history[-3:] if len(history) >= 3 else history
        router_messages.insert(1, {"role": "system", "content": f"HISTORIAL RECIENTE:\n{json.dumps(historial_breve, ensure_ascii=False)}"})

    intent_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=router_messages,
        temperature=0.1,
        response_format={"type": "json_object"}
    )

    raw_router = intent_response.choices[0].message.content.strip()
    router_json = safe_json_loads(raw_router)
    
    raw_topic = router_json.get("topic", "general")
    topic = normalize_topic(raw_topic)

    rag_context = ""
    if router_json.get("needs_rag", True):
        rag_context = rag.get_knowledge(user_message, topic=topic)

    pcap_context = f"Datos de Scapy: {pcap_data}" if pcap_data else "No hay archivo subido aún."

    full_system_prompt = SYSTEM_PROMPT_GENERAL_TUTOR.format(
        intent_json=json.dumps(router_json, ensure_ascii=False)
    ) + f"\n\nCONTEXTO TÉCNICO (RAG):\n{rag_context if rag_context else 'No se recuperó contexto técnico adicional.'}\n\nDATOS DE LA CAPTURA (SCAPY):\n{pcap_context}"

    messages_to_send = [{"role": "system", "content": full_system_prompt}]
    if history:
        messages_to_send.extend(history)
    else:
        messages_to_send.append({"role": "user", "content": user_message})

    final_response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages_to_send,
        temperature=0.2,
    )
    return {
        "response": final_response.choices[0].message.content,
        "router": router_json
    }

# =========================
# PCAP ANALYSIS
# =========================

def get_pcap_analysis_response(
    pcap_data: dict,
    history: Optional[List[Dict[str, str]]] = None,
) -> str:
    prompt = SYSTEM_PROMPT_PCAP_ANALYSIS.format(pcap_summary=str(pcap_data))

    messages_to_send = [{"role": "system", "content": prompt}]

    if history:
        messages_to_send.extend(history)
    else:
        messages_to_send.append(
            {
                "role": "user",
                "content": "Analiza los datos del PCAP y guía mi aprendizaje de acuerdo a las reglas establecidas."
            }
        )

    final_response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=messages_to_send,
        temperature=0.2,
    )

    return final_response.choices[0].message.content

# =========================
# ESCENARIOS
# =========================

def generate_scenario_data(nivel_id: int):
    global rag
    if rag is None:
        init_rag_service()

    topic_map = {
        1: "texto_plano",
        2: "http_phishing",
        3: "port_scan",
        4: "dos",
        5: "malware_c2",
    }

    topic = topic_map.get(nivel_id, "general")
    contexto_rag = rag.get_knowledge(
        f"Análisis técnico de {topic}",
        topic=topic,
    )

    prompt = SYSTEM_PROMPT_SCENARIO_DESIGNER + f"""

TOPICO: {topic}
NIVEL: {nivel_id}
CONTEXTO_RAG:
{contexto_rag if contexto_rag else "Información general de seguridad"}
"""

    print("\n" + "=" * 80)
    print("SCENARIO DESIGNER - INPUT")
    print("-" * 80)
    print(f"NIVEL: {nivel_id}")
    print(f"TOPIC: {topic}")
    print("RAG CONTEXT:")
    print(_clip_text(contexto_rag or "vacío", 3000))
    print("=" * 80 + "\n")

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": prompt}],
        temperature=0.8,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content
    print("\n" + "=" * 80)
    print("SCENARIO DESIGNER - RAW OUTPUT")
    print("-" * 80)
    print(_clip_text(raw, 4000))
    print("=" * 80 + "\n")

    return json.loads(raw)