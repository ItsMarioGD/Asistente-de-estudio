"""Asistente de Estudio Universitario — UI principal con Streamlit."""
import io
import sys
from pathlib import Path

# Asegurar que src/ sea importable cuando se ejecuta con `streamlit run`
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pypdf

from src.config import (
    VAULT_DIR, VOCALES_ES, DEFAULT_VOICE, RESUMEN_LONGITUD,
)
from src.ingest import (
    cargar_url, guardar_en_vault, preparar_chunks,
)
from src.rag import indexar, buscar, listar_fuentes, listar_materias, total_chunks, texto_por_fuente
from src.llm import (
    resumir_documento, resumir_materia, responder_pregunta, glosario,
)
from src.tts import generar_audio, reproducir, detener, esta_reproduciendo


def leer_pdf_desde_buffer(uploaded_file) -> str:
    """Lee un PDF subido por Streamlit (UploadedFile) directamente desde memoria."""
    raw = uploaded_file.read()
    reader = pypdf.PdfReader(io.BytesIO(raw))
    paginas = []
    for page in reader.pages:
        try:
            paginas.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n\n".join(p for p in paginas if p.strip())


st.set_page_config(page_title="Asistente de Estudio", page_icon="📚", layout="wide")

# --- Estado de sesión ---
def _init_state():
    defaults = {
        "materia_seleccionada": None,
        "voz": DEFAULT_VOICE,
        "velocidad": 1.0,
        "chat_historial": [],
        "ultimo_audio": None,
        "ultima_respuesta": "",
        "ultimo_resumen": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# --- Sidebar ---
with st.sidebar:
    st.title("⚙️ Configuración")

    st.session_state.voz = st.selectbox(
        "Voz para audiolibro",
        options=list(VOCALES_ES.values()),
        index=list(VOCALES_ES.values()).index(st.session_state.voz)
              if st.session_state.voz in VOCALES_ES.values() else 0,
        format_func=lambda v: next((k for k, val in VOCALES_ES.items() if val == v), v),
    )

    st.session_state.velocidad = st.slider(
        "Velocidad", min_value=0.8, max_value=1.3, value=st.session_state.velocidad, step=0.05,
    )

    st.divider()
    st.subheader("📂 Materias")
    materias = listar_materias()
    if materias:
        materia_choice = st.radio(
            "Filtrar por materia",
            options=["(todas)"] + materias,
            index=0,
        )
        st.session_state.materia_seleccionada = (
            None if materia_choice == "(todas)" else materia_choice
        )
    else:
        st.info("Sube tu primer documento en la pestaña 'Biblioteca'.")

    st.divider()
    st.caption(f"Chunks indexados: {total_chunks()}")


# --- Tabs principales ---
tab_biblio, tab_resumen, tab_pregunta, tab_audio = st.tabs(
    ["📚 Biblioteca", "📝 Resumen", "💬 Preguntar", "🔊 Audiolibro"]
)


# ============ BIBLIOTECA ============
with tab_biblio:
    st.header("📚 Biblioteca de recursos")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Subir PDF o texto")
        with st.form("form_subir_pdf", clear_on_submit=False):
            materia_nueva = st.text_input(
                "Materia (ej. Cálculo II)",
                key="materia_nueva",
                placeholder="Escribe aquí el nombre de la materia",
            )
            archivos = st.file_uploader(
                "Arrastra uno o varios PDFs / .txt / .md",
                type=["pdf", "txt", "md"],
                accept_multiple_files=True,
            )
            submitted = st.form_submit_button("💾 Guardar e indexar")

        if submitted:
            materia_limpia = (materia_nueva or "").strip()
            if not materia_limpia:
                st.error("⚠ Primero escribe el nombre de la materia arriba.")
            elif not archivos:
                st.error("⚠ Selecciona al menos un archivo para subir.")
            else:
                progreso = st.progress(0.0, text="Procesando...")
                total_idx = 0
                errores = []
                for i, f in enumerate(archivos):
                    try:
                        nombre_lower = f.name.lower()
                        if nombre_lower.endswith(".pdf"):
                            contenido = leer_pdf_desde_buffer(f)
                        else:
                            contenido = f.read().decode("utf-8", errors="ignore")

                        if not contenido.strip():
                            errores.append(f"{f.name} (sin texto extraíble)")
                        else:
                            nombre = f"{materia_limpia}__{f.name}"
                            guardar_en_vault(nombre, contenido)
                            chunks = preparar_chunks(
                                contenido, fuente=nombre, materia=materia_limpia,
                            )
                            total_idx += indexar(chunks)
                    except Exception as e:
                        errores.append(f"{f.name} ({e})")
                    progreso.progress((i + 1) / len(archivos),
                                      text=f"Procesado {i+1}/{len(archivos)}")
                progreso.empty()
                if total_idx > 0:
                    st.success(f"✅ Listo: {total_idx} chunks indexados en '{materia_limpia}'.")
                if errores:
                    st.warning("Problemas: " + "; ".join(errores))
                st.rerun()

    with col2:
        st.subheader("Agregar desde URL")
        with st.form("form_subir_url", clear_on_submit=False):
            materia_url = st.text_input(
                "Materia para este enlace", key="materia_url",
                placeholder="Ej. Historia, Biología...",
            )
            url = st.text_input(
                "URL (artículo, blog académico, etc.)",
                placeholder="https://...",
            )
            submitted_url = st.form_submit_button("🌐 Descargar e indexar")
        if submitted_url:
            materia_limpia = (materia_url or "").strip()
            url_limpia = (url or "").strip()
            if not materia_limpia:
                st.error("⚠ Escribe la materia para clasificar el enlace.")
            elif not url_limpia:
                st.error("⚠ Pega una URL válida.")
            else:
                with st.spinner("Descargando y procesando..."):
                    try:
                        texto = cargar_url(url_limpia)
                        if not texto.strip():
                            st.error("No se pudo extraer texto de esa URL.")
                        else:
                            nombre = f"{materia_limpia}__web_{abs(hash(url_limpia))}.txt"
                            guardar_en_vault(nombre, texto)
                            chunks = preparar_chunks(
                                texto, fuente=nombre, materia=materia_limpia,
                            )
                            n = indexar(chunks)
                            st.success(f"✅ Indexado: {n} chunks desde la URL.")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")

    st.divider()
    st.subheader("Documentos cargados")
    fuentes = listar_fuentes()
    if fuentes:
        for f in fuentes:
            st.markdown(f"- **{f['fuente']}** — materia: `{f['materia']}`")
    else:
        st.info("Aún no has subido ningún documento.")


# ============ RESUMEN ============
with tab_resumen:
    st.header("📝 Resúmenes")

    fuentes = listar_fuentes()
    if not fuentes:
        st.info("Primero sube documentos en 'Biblioteca'.")
    else:
        modo = st.radio("Modo", ["Por documento", "Por materia completa"],
                        horizontal=True)
        if modo == "Por documento":
            nombre_doc = st.selectbox(
                "Documento",
                options=[f["fuente"] for f in fuentes],
            )
            longitud = st.select_slider(
                "Longitud", options=list(RESUMEN_LONGITUD.keys()),
            )
            palabras = RESUMEN_LONGITUD[longitud]
            if st.button("✨ Generar resumen"):
                with st.spinner(f"Resumiendo con {palabras} palabras objetivo..."):
                    texto = texto_por_fuente(nombre_doc)
                    if not texto.strip():
                        st.error("No hay texto indexado para este documento.")
                        st.stop()
                    resumen = resumir_documento(
                        texto, longitud_palabras=palabras, fuente=nombre_doc,
                    )
                    st.session_state.ultimo_resumen = resumen
                    st.session_state.ultimo_audio = None
                st.markdown("### Resumen")
                st.markdown(resumen)

                if st.button("🔊 Reproducir este resumen"):
                    with st.spinner("Generando audio..."):
                        ruta_audio = generar_audio(
                            resumen, st.session_state.voz, st.session_state.velocidad,
                        )
                        st.session_state.ultimo_audio = str(ruta_audio)
                        reproducir(ruta_audio)
                    st.success("Reproduciendo.")
        else:
            materia = st.selectbox("Materia", options=listar_materias())
            longitud = st.select_slider(
                "Longitud", options=list(RESUMEN_LONGITUD.keys()),
            )
            palabras = RESUMEN_LONGITUD[longitud]
            if st.button("✨ Generar resumen de la materia"):
                with st.spinner(f"Sintetizando la materia '{materia}'..."):
                    chunks = buscar("resumen general de la materia", k=40, materia=materia)
                    resumen = resumir_materia(chunks, palabras, materia)
                    st.session_state.ultimo_resumen = resumen
                    st.session_state.ultimo_audio = None
                st.markdown("### Resumen de la materia")
                st.markdown(resumen)
                if st.button("🔊 Reproducir resumen de la materia"):
                    with st.spinner("Generando audio..."):
                        ruta_audio = generar_audio(
                            resumen, st.session_state.voz, st.session_state.velocidad,
                        )
                        st.session_state.ultimo_audio = str(ruta_audio)
                        reproducir(ruta_audio)
                    st.success("Reproduciendo.")


# ============ PREGUNTAS ============
with tab_pregunta:
    st.header("💬 Pregúntale a tus documentos")

    if total_chunks() == 0:
        st.info("Sube documentos primero.")
    else:
        pregunta = st.chat_input("Escribe tu pregunta sobre el material...")
        if pregunta:
            with st.chat_message("user"):
                st.markdown(pregunta)
            with st.spinner("Buscando en tus documentos..."):
                chunks = buscar(
                    pregunta,
                    materia=st.session_state.materia_seleccionada,
                )
                respuesta = responder_pregunta(
                    pregunta, chunks, historial=st.session_state.chat_historial,
                )
                st.session_state.chat_historial.append({"role": "user", "content": pregunta})
                st.session_state.chat_historial.append({"role": "assistant", "content": respuesta})
                st.session_state.ultima_respuesta = respuesta
                st.session_state.ultimo_audio = None
            with st.chat_message("assistant"):
                st.markdown(respuesta)
                if st.button("🔊 Escuchar respuesta", key=f"audio_resp_{len(st.session_state.chat_historial)}"):
                    with st.spinner("Generando audio..."):
                        ruta_audio = generar_audio(
                            respuesta, st.session_state.voz, st.session_state.velocidad,
                        )
                        st.session_state.ultimo_audio = str(ruta_audio)
                        reproducir(ruta_audio)
                    st.success("Reproduciendo.")

        if st.button("🧹 Limpiar conversación"):
            st.session_state.chat_historial = []
            st.rerun()

        # Historial
        if st.session_state.chat_historial:
            st.divider()
            st.subheader("Conversación")
            for msg in st.session_state.chat_historial:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])


# ============ AUDIOLIBRO ============
with tab_audio:
    st.header("🔊 Reproductor de audiolibros")

    st.write(
        f"Reproduciendo ahora: **{'Sí' if esta_reproduciendo() else 'No'}**"
    )

    if st.session_state.ultimo_audio and _P(st.session_state.ultimo_audio).exists():
        st.audio(st.session_state.ultimo_audio)
    elif st.session_state.ultimo_resumen:
        st.info("No hay audio aún. Genera uno desde 'Resumen' o 'Preguntar'.")

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("⏹ Detener"):
            detener()
            st.success("Detenido.")
    with c2:
        if st.button("▶ Reanudar último") and st.session_state.ultimo_audio:
            reproducir(_P(st.session_state.ultimo_audio))
    with c3:
        if st.session_state.ultimo_audio:
            with open(st.session_state.ultimo_audio, "rb") as f:
                st.download_button(
                    "⬇ Descargar MP3",
                    data=f.read(),
                    file_name=_P(st.session_state.ultimo_audio).name,
                    mime="audio/mpeg",
                )

    st.divider()
    st.caption(
        "Tip: los audios se generan por primera vez y luego quedan en cache. "
        "Cambia la voz o velocidad en el panel lateral para regenerarlos."
    )