# 📚 Asistente de Estudio Universitario

Aplicación local en Python que centraliza tus recursos universitarios, los resume con IA, los lee con voz natural y te permite hacer preguntas sobre el contenido.

## ¿Qué hace?

- **Sube** tus PDFs, apuntes (`.txt` / `.md`) o enlaces web y etiquétalos por materia.
- **Resume** cualquier documento o toda una materia en versión corta, media o larga.
- **Lee en voz alta** los resúmenes (y respuestas) con voces de Microsoft en español (España, México o Argentina).
- **Responde preguntas** basándose solo en *tus* documentos, citando la fuente.

Todo corre **local** con Ollama: tu material nunca sale de tu computador (excepto el texto a voz, que se envía a las voces de Microsoft —solo el texto, no los PDFs).

## Requisitos

1. **Python 3.10+** (probado con 3.14).
2. **Ollama** instalado: <https://ollama.com/download>
3. ~6 GB de disco para los modelos.
4. Conexión a internet solo la primera vez (para descargar modelos y generar audio).

## Instalación (Windows, primera vez)

**Opción recomendada — todo automático con doble clic:**

1. Doble clic en **`instalar.bat`**. Crea el entorno virtual, instala las dependencias y descarga los modelos de IA (~5 GB; puede tardar varios minutos).
2. Doble clic en **`run.bat`** cada vez que quieras usar la app.

**Opción manual (terminal):**

```bash
ollama pull llama3.1:8b
ollama pull nomic-embed-text

cd asistente-estudio
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Ejecución

Doble clic en **`run.bat`**. La ventana de CMD se quedará abierta mientras la app esté corriendo y mostrará la URL.

- URL: <http://localhost:8501>
- Si el navegador no se abre solo, copia esa URL manualmente.
- Para detener la app: cierra la ventana de CMD o pulsa `Ctrl+C` dentro de ella.

## Flujo de uso

1. **Biblioteca** → sube un PDF o pega una URL. Asigna una materia (ej. *Cálculo II*).
2. **Resumen** → elige documento o materia completa, longitud y pulsa "Generar resumen". Luego "Reproducir".
3. **Preguntar** → escribe tu pregunta; la IA responde con citas a tus archivos.
4. **Audiolibro** → reproduce, pausa, descarga el MP3 o regenera con otra voz/velocidad (panel lateral).

## Configuración

Edita `src/config.py` para:
- Cambiar el modelo de IA (`LLM_MODEL`, `EMBED_MODEL`).
- Ajustar tamaños de chunk (`CHUNK_SIZE`, `CHUNK_OVERLAP`).
- Añadir voces a `VOCALES_ES`.

Si tu computador es más limitado, cambia `LLM_MODEL` a `llama3.2:3b` y vuelve a correr `ollama pull llama3.2:3b`.

## Estructura

```
asistente-estudio/
├── app.py              # UI Streamlit
├── src/
│   ├── config.py       # Rutas, modelos, voces
│   ├── ingest.py       # Carga PDFs/URLs y chunking
│   ├── rag.py          # ChromaDB + embeddings
│   ├── llm.py          # Prompts de resumen y Q&A
│   └── tts.py          # Edge TTS + pygame
├── data/               # Generado al indexar (ignorado en git)
│   ├── vault/          # Documentos originales
│   └── chroma/         # Base vectorial
├── audio/              # MP3 cacheados (ignorado en git)
├── requirements.txt
├── instalar.bat        # Instalación inicial (crea venv + modelos)
└── run.bat             # Arranca la app con doble clic
```

## Privacidad

- Los documentos y embeddings se guardan **solo en tu disco** (`data/`).
- Los resúmenes y respuestas se generan localmente con Ollama.
- Solo el texto a voz pasa por las voces de Microsoft (necesario para la síntesis, no guarda contenido).