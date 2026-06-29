"""Ingesta de documentos: PDFs, URLs, txt/md y chunking."""
import re
from pathlib import Path
from typing import List, Dict

import pypdf
import trafilatura

from .config import VAULT_DIR


def cargar_pdf(path: Path) -> str:
    """Extrae texto de un PDF página por página."""
    reader = pypdf.PdfReader(str(path))
    paginas = []
    for i, page in enumerate(reader.pages):
        try:
            texto = page.extract_text() or ""
        except Exception:
            texto = ""
        if texto.strip():
            paginas.append(texto)
    return "\n\n".join(paginas)


def cargar_url(url: str) -> str:
    """Descarga una página web y extrae el texto principal con trafilatura."""
    descargado = trafilatura.fetch_url(url)
    if descargado is None:
        raise RuntimeError(f"No se pudo descargar: {url}")
    texto = trafilatura.extract(descargado, include_comments=False, include_tables=False)
    if not texto:
        raise RuntimeError(f"No se pudo extraer texto de: {url}")
    return texto


def cargar_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def guardar_en_vault(nombre: str, contenido: str) -> Path:
    """Guarda un texto en data/vault/<nombre>.txt y devuelve la ruta."""
    destino = VAULT_DIR / nombre
    if not destino.suffix:
        destino = destino.with_suffix(".txt")
    destino.write_text(contenido, encoding="utf-8")
    return destino


def _limpiar_texto(texto: str) -> str:
    """Normaliza espacios y saltos de línea."""
    texto = texto.replace("\r\n", "\n")
    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


def chunkear(texto: str, tam: int = 500, overlap: int = 50) -> List[str]:
    """
    Divide un texto largo en chunks de ~`tam` palabras con `overlap` palabras
    de solapamiento. Divide primero por párrafos para no cortar ideas.
    """
    texto = _limpiar_texto(texto)
    if not texto:
        return []

    parrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    chunks: List[str] = []
    buffer: List[str] = []
    buffer_palabras = 0

    def vaciar_buffer():
        nonlocal buffer, buffer_palabras
        if buffer:
            chunks.append(" ".join(buffer).strip())
            # Mantener las últimas `overlap` palabras como contexto
            palabras = " ".join(buffer).split()
            if len(palabras) > overlap:
                cola = " ".join(palabras[-overlap:])
                buffer = [cola]
                buffer_palabras = overlap
            else:
                buffer = []
                buffer_palabras = 0

    for parrafo in parrafos:
        palabras_parrafo = parrafo.split()
        # Si el párrafo solo excede el tamaño, partirlo en oraciones
        if len(palabras_parrafo) > tam:
            vaciar_buffer()
            oraciones = re.split(r"(?<=[.!?])\s+", parrafo)
            mini_buf: List[str] = []
            mini_count = 0
            for oracion in oraciones:
                w = oracion.split()
                if mini_count + len(w) > tam and mini_buf:
                    chunks.append(" ".join(mini_buf).strip())
                    mini_buf = w[-overlap:] if overlap and len(w) > overlap else []
                    mini_count = len(mini_buf)
                else:
                    mini_buf.append(oracion)
                    mini_count += len(w)
            if mini_buf:
                chunks.append(" ".join(mini_buf).strip())
            continue

        if buffer_palabras + len(palabras_parrafo) > tam:
            vaciar_buffer()
        buffer.append(parrafo)
        buffer_palabras += len(palabras_parrafo)

    vaciar_buffer()
    return [c for c in chunks if c]


def preparar_chunks(texto: str, fuente: str, materia: str) -> List[Dict]:
    """
    Devuelve una lista de dicts con `texto`, `fuente` y `materia`,
    listos para indexar en ChromaDB.
    """
    pedazos = chunkear(texto)
    return [
        {
            "id": f"{fuente}::{i}",
            "texto": p,
            "metadata": {"fuente": fuente, "materia": materia, "chunk_idx": i},
        }
        for i, p in enumerate(pedazos)
    ]