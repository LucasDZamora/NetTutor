import re
from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# =========================
# LIMPIEZA AVANZADA PDF
# =========================

def clean_text(t: str) -> str:
    """
    Limpieza pensada para PDFs técnicos:
    - RFCs
    - MITRE
    - libros Nmap
    - papers
    - documentación OWASP
    """

    if not t:
        return ""

    # -------------------------
    # caracteres basura
    # -------------------------
    t = t.replace("\x00", " ")
    t = t.replace("\uf0b7", " ")  # bullets raros
    t = t.replace("\u200b", " ")  # zero width space

    # -------------------------
    # unir palabras cortadas
    # ex:
    # connec-
    # tion
    # -------------------------
    t = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', t)

    # -------------------------
    # convertir saltos múltiples
    # -------------------------
    t = re.sub(r'\n{2,}', '\n', t)

    # -------------------------
    # eliminar headers/footers RFC comunes
    # ejemplos:
    # RFC 854 TELNET PROTOCOL SPECIFICATION May 1983
    # Page 5
    # -------------------------
    t = re.sub(r'RFC\s+\d+.*?\n', ' ', t)
    t = re.sub(r'Page\s+\d+', ' ', t)

    # -------------------------
    # eliminar URLs repetidas
    # -------------------------
    t = re.sub(r'https?://\S+', ' ', t)

    # -------------------------
    # eliminar líneas extremadamente cortas
    # típicas de headers rotos
    # -------------------------
    lines = []

    for line in t.split("\n"):
        line = line.strip()

        if not line:
            continue

        # elimina líneas basura pequeñas
        if len(line) <= 2:
            continue

        lines.append(line)

    t = "\n".join(lines)

    # -------------------------
    # colapsar espacios
    # -------------------------
    t = re.sub(r'[ \t]+', ' ', t)

    # -------------------------
    # preservar saltos semánticos
    # -------------------------
    t = re.sub(r'\n\s+', '\n', t)

    # -------------------------
    # normalizar whitespace
    # -------------------------
    t = re.sub(r'\s+\n', '\n', t)

    # -------------------------
    # eliminar exceso final
    # -------------------------
    t = t.strip()

    return t


# =========================
# SPLIT ORACIONES
# =========================

def split_sentences(t: str):

    t = clean_text(t)

    if not t:
        return []

    protected = {
        "e.g.": "eg__DOT__",
        "i.e.": "ie__DOT__",
        "Fig.": "Fig__DOT__",
        "No.": "No__DOT__",
        "Dr.": "Dr__DOT__",
        "Mr.": "Mr__DOT__",
        "Ms.": "Ms__DOT__",
        "etc.": "etc__DOT__",
        "RFC.": "RFC__DOT__",
    }

    for k, v in protected.items():
        t = t.replace(k, v)

    # división oración
    sents = re.split(r'(?<=[.!?])\s+', t)

    out = []

    for s in sents:

        s = s.strip()

        for k, v in protected.items():
            s = s.replace(v, k)

        # filtra basura
        if len(s) < 30:
            continue

        out.append(s)

    return out


# =========================
# CHUNKING SEMÁNTICO
# =========================

def chunk_text_sentences(
    t: str,
    max_sentences: int = 4,
    overlap: int = 1,
    min_chars: int = 200,
    max_chars: int = 1200
):

    sents = split_sentences(t)

    if not sents:
        return []

    chunks = []

    step = max(1, max_sentences - overlap)

    i = 0

    while i < len(sents):

        current = []
        current_len = 0

        for j in range(i, min(i + max_sentences, len(sents))):

            sent = sents[j]

            if not sent:
                continue

            # evita chunks gigantes
            if current and (current_len + len(sent) > max_chars):
                break

            current.append(sent)

            current_len += len(sent)

        chunk = " ".join(current).strip()

        # evita chunks inútiles
        if chunk and len(chunk) >= min_chars:

            # limpia final extra
            chunk = re.sub(r'\s+', ' ', chunk)

            chunks.append(chunk)

        i += step

    return chunks


# =========================
# DETECTAR TOPIC
# =========================

def infer_topic(filename: str):

    f = filename.lower()

    if "nmap" in f:
        return "port_scan"

    if "rfc854" in f or "telnet" in f:
        return "telnet"

    if "rfc1939" in f or "pop3" in f:
        return "pop3"

    if "mitre" in f or "beacon" in f:
        return "malware_c2"

    if "ddos" in f or "flood" in f:
        return "dos"

    if "http" in f or "owasp" in f:
        return "http_phishing"

    return "unknown"


# =========================
# CARGAR PDFs
# =========================

def load_pdf_texts(pdf_dir: str):

    pdf_paths = sorted(Path(pdf_dir).rglob("*.pdf"))

    docs = []

    for pdf_path in pdf_paths:

        print(f"Cargando: {pdf_path.name}")

        loader = PyPDFLoader(str(pdf_path))

        pdf_docs = loader.load()

        for page_num, d in enumerate(pdf_docs):

            cleaned = clean_text(d.page_content)

            # evita páginas vacías/basura
            if len(cleaned) < 80:
                continue

            d.page_content = cleaned

            d.metadata["source_file"] = pdf_path.name
            d.metadata["page"] = page_num + 1
            d.metadata["topic"] = infer_topic(pdf_path.name)

            docs.append(d)

    return docs


# =========================
# INGESTA PRINCIPAL
# =========================

def run_ingestion():

    # -------------------------
    # cargar PDFs
    # -------------------------
    docs = load_pdf_texts("data/docs/")

    all_chunks = []
    all_metas = []

    # -------------------------
    # chunking
    # -------------------------
    for doc in docs:

        text = doc.page_content

        if not text:
            continue

        chunks = chunk_text_sentences(
            text,
            max_sentences=4,
            overlap=1,
            min_chars=200,
            max_chars=1200
        )

        for idx, ch in enumerate(chunks):

            meta = dict(doc.metadata)

            meta["chunk_id"] = idx

            all_chunks.append(ch)
            all_metas.append(meta)

    print(f"Chunks generados: {len(all_chunks)}")

    # -------------------------
    # embeddings multilingüe
    # -------------------------
    embeddings = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={
            "device": "cpu"
        },
        encode_kwargs={
            "normalize_embeddings": True
        }
    )

    # -------------------------
    # chroma db
    # -------------------------
    vectorstore = Chroma.from_texts(
        texts=all_chunks,
        embedding=embeddings,
        metadatas=all_metas,
        persist_directory="data/chroma_db"
    )

    print("Base de conocimientos lista.")


if __name__ == "__main__":
    run_ingestion()