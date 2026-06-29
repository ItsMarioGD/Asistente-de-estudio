"""Configuración central del Asistente de Estudio."""
from pathlib import Path

# Rutas del proyecto
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VAULT_DIR = DATA_DIR / "vault"
CHROMA_DIR = DATA_DIR / "chroma"
AUDIO_DIR = PROJECT_ROOT / "audio"

# Crear carpetas si no existen
for _d in (DATA_DIR, VAULT_DIR, CHROMA_DIR, AUDIO_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# Modelos Ollama
LLM_MODEL = "llama3.1:8b"           # Generación (resúmenes, Q&A)
EMBED_MODEL = "nomic-embed-text"    # Embeddings para RAG

# Chunking
CHUNK_SIZE = 500          # palabras por chunk
CHUNK_OVERLAP = 50        # palabras de solapamiento entre chunks

# Retrieval
RETRIEVAL_K = 8           # chunks relevantes a recuperar por consulta

# Voces Edge TTS disponibles (español)
VOCALES_ES = {
    "Elvira (España, femenina)":  "es-ES-ElviraNeural",
    "Alvaro (España, masculina)": "es-ES-AlvaroNeural",
    "Dalia (México, femenina)":   "es-MX-DaliaNeural",
    "Jorge (México, masculino)":  "es-MX-JorgeNeural",
    "Elena (Argentina, fem.)":    "es-AR-ElenaNeural",
    "Tomas (Argentina, masc.)":   "es-AR-TomasNeural",
}
DEFAULT_VOICE = "es-ES-ElviraNeural"

# Longitudes de resumen (palabras objetivo)
RESUMEN_LONGITUD = {
    "Corto (TL;DR, ~100 palabras)": 100,
    "Medio (audiolibro, ~250 palabras)": 250,
    "Largo (estudio profundo, ~500 palabras)": 500,
}

# Colección ChromaDB
COLLECTION_NAME = "estudio"

# Host Ollama
OLLAMA_HOST = "http://127.0.0.1:11434"