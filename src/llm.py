"""Capa LLM: resúmenes y Q&A con citas, usando Ollama."""
from typing import List, Dict, Optional

import ollama

from .config import LLM_MODEL


def _chat(messages: List[Dict], temperature: float = 0.3) -> str:
    """Wrapper simple alrededor de Ollama chat."""
    resp = ollama.chat(
        model=LLM_MODEL,
        messages=messages,
        options={"temperature": temperature},
    )
    return resp["message"]["content"].strip()


def resumir_documento(texto: str, longitud_palabras: int = 250,
                      fuente: str = "") -> str:
    """Genera un resumen estructurado en español."""
    sys = (
        "Eres un asistente académico que ayuda a estudiantes universitarios. "
        "Resumes de forma clara, densa y precisa en español. "
        "Estructura el resumen con secciones y viñetas cuando ayude."
    )
    user = (
        f"Resume el siguiente contenido en aproximadamente {longitud_palabras} palabras. "
        f"Incluye:\n"
        f"1. Una línea con la idea central.\n"
        f"2. Puntos clave (viñetas).\n"
        f"3. Conceptos importantes o definiciones.\n"
        f"4. Conclusión o implicación (si aplica).\n\n"
        f"Fuente: {fuente}\n\n"
        f"---CONTENIDO---\n{texto}"
    )
    return _chat([
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ])


def resumir_materia(chunks: List[Dict], longitud_palabras: int = 350,
                    materia: str = "") -> str:
    """Resume el conjunto de chunks de una materia completa."""
    contexto = "\n\n---\n\n".join(c["texto"] for c in chunks[:40])
    sys = (
        "Eres un asistente académico. Sintetizas múltiples documentos de un mismo "
        "tema en una narrativa coherente y estructurada en español."
    )
    user = (
        f"Tienes varios fragmentos de la materia '{materia}'. Produce un resumen "
        f"consolidado de unas {longitud_palabras} palabras que sirva como "
        f"'audiolibro' para entender el tema de principio a fin. "
        f"Usa secciones (Introducción, Conceptos clave, Desarrollo, Cierre).\n\n"
        f"---FRAGMENTOS---\n{contexto}"
    )
    return _chat([
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ])


def responder_pregunta(query: str, chunks: List[Dict],
                       historial: Optional[List[Dict]] = None) -> str:
    """Responde una pregunta basándose SOLO en los chunks provistos."""
    if not chunks:
        return ("No encontré información relevante en tus documentos sobre esa "
                "pregunta. Sube más recursos o reformúlala.")

    contexto = []
    for i, c in enumerate(chunks, 1):
        meta = c["metadata"]
        contexto.append(
            f"[Fuente {i}] archivo={meta.get('fuente','?')}, "
            f"materia={meta.get('materia','?')}\n{c['texto']}"
        )
    contexto_txt = "\n\n".join(contexto)

    sys = (
        "Eres un asistente académico. Respondes preguntas en español basándote "
        "EXCLUSIVAMENTE en el contexto proporcionado. Si la respuesta no está en "
        "el contexto, dilo claramente. Cuando cites información, referencia el "
        "número de fuente entre corchetes, por ejemplo [Fuente 1]."
    )
    user = (
        f"CONTEXTO DE TUS DOCUMENTOS:\n{contexto_txt}\n\n"
        f"PREGUNTA: {query}\n\n"
        f"Responde de forma clara y, cuando uses información del contexto, "
        f"indica la fuente entre corchetes."
    )

    messages = [{"role": "system", "content": sys}]
    if historial:
        # Mantener solo las últimas 4 interacciones para no saturar
        messages.extend(historial[-8:])
    messages.append({"role": "user", "content": user})
    return _chat(messages)


def glosario(texto: str) -> str:
    """Genera un glosario de términos clave a partir de un texto."""
    sys = "Eres un asistente académico. Produces glosarios claros en español."
    user = (
        "Del siguiente contenido, extrae los 10 términos o conceptos más "
        "importantes y defínelos brevemente (1-2 líneas cada uno) en formato "
        "markdown.\n\n---CONTENIDO---\n" + texto
    )
    return _chat([
        {"role": "system", "content": sys},
        {"role": "user", "content": user},
    ])