"""RAG: base vectorial ChromaDB con embeddings generados por Ollama."""
from typing import List, Dict, Optional
import chromadb
from chromadb.api.models.Collection import Collection

from .config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL, RETRIEVAL_K


_client = chromadb.PersistentClient(path=str(CHROMA_DIR))


def _coleccion() -> Collection:
    return _client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def _embed(textos: List[str]) -> List[List[float]]:
    """Genera embeddings usando Ollama (nomic-embed-text)."""
    import ollama
    vectores = []
    for t in textos:
        resp = ollama.embeddings(model=EMBED_MODEL, prompt=t)
        vectores.append(resp["embedding"])
    return vectores


def indexar(chunks: List[Dict]) -> int:
    """
    Recibe una lista de dicts con keys: id, texto, metadata.
    Devuelve la cantidad efectivamente indexada.
    """
    if not chunks:
        return 0
    col = _coleccion()
    # Evitar duplicados si se vuelve a procesar el mismo chunk
    ids_existentes = set(col.get(ids=[c["id"] for c in chunks]).get("ids", []))
    nuevos = [c for c in chunks if c["id"] not in ids_existentes]
    if not nuevos:
        return 0

    embeddings = _embed([c["texto"] for c in nuevos])
    col.add(
        ids=[c["id"] for c in nuevos],
        documents=[c["texto"] for c in nuevos],
        embeddings=embeddings,
        metadatas=[c["metadata"] for c in nuevos],
    )
    return len(nuevos)


def buscar(query: str, k: int = RETRIEVAL_K,
           materia: Optional[str] = None) -> List[Dict]:
    """Devuelve los `k` chunks más relevantes, opcionalmente filtrados por materia."""
    col = _coleccion()
    where = {"materia": materia} if materia else None
    emb = _embed([query])[0]
    res = col.query(query_embeddings=[emb], n_results=k, where=where)
    documentos = (res.get("documents") or [[]])[0]
    metadatos = (res.get("metadatas") or [[]])[0]
    return [
        {"texto": d, "metadata": m}
        for d, m in zip(documentos, metadatos)
    ]


def listar_fuentes() -> List[Dict]:
    """Devuelve las fuentes indexadas con su materia."""
    col = _coleccion()
    data = col.get(include=["metadatas"])
    seen = {}
    for meta in data.get("metadatas", []):
        if not meta:
            continue
        f = meta.get("fuente", "?")
        m = meta.get("materia", "Sin materia")
        seen[f] = m
    return [{"fuente": f, "materia": m} for f, m in sorted(seen.items())]


def listar_materias() -> List[str]:
    return sorted({s["materia"] for s in listar_fuentes()})


def total_chunks() -> int:
    col = _coleccion()
    return col.count()


def texto_por_fuente(fuente: str) -> str:
    """Recupera el texto completo indexado para una fuente (uniendo chunks)."""
    col = _coleccion()
    data = col.get(where={"fuente": fuente}, include=["documents", "metadatas"])
    docs = data.get("documents", [])
    metas = data.get("metadatas", [])
    pares = sorted(
        zip(metas, docs),
        key=lambda x: x[0].get("chunk_idx", 0),
    )
    return "\n\n".join(d for _, d in pares)