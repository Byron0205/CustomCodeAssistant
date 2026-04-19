# Sistema RAG Local (Retrieval-Augmented Generation)

Un sistema de búsqueda y generación de respuestas basado en documentos locales, sin dependencias de servicios externos en la nube.

## 🎯 ¿Qué es este proyecto?

Este es un **sistema RAG local** que permite hacer preguntas sobre tus documentos. Funciona en dos etapas:

1. **Indexación**: Procesa tus documentos y crea una base de datos vectorial
2. **Consulta**: Busca información relevante y genera respuestas con contexto

Todo funciona localmente en tu máquina. No se envía ningún dato a internet.

---

## 🏗️ Arquitectura

### **Etapa 1: Indexación** (`indexar.py`)
Procesa documentos de `./docs/`:
- Lee archivos `.md`, `.txt`, `.py`
- Divide el contenido en **chunks de 800 tokens** con solapamiento de 100 tokens (para mantener contexto)
- Genera **embeddings** (representaciones numéricas) usando el modelo `nomic-embed-text`
- Almacena todo en **ChromaDB** (`./chroma_db/`)

**Cuándo ejecutar**: Cada vez que agregues o modifiques documentos en `./docs/`

```bash
pipenv run python indexar.py
```

### **Etapa 2: Consulta** (`consultar.py`)
Carga la base de datos vectorial y permite hacer preguntas:
- Busca los **5 chunks más relevantes** para tu pregunta
- Envía esos fragmentos al LLM `qwen2.5-coder:3b`
- Genera una respuesta contextualizada
- Muestra las **fuentes utilizadas**

```bash
pipenv run python consultar.py
```

---

## 🔧 Requisitos Previos

### Ollama
Debe estar ejecutando localmente con dos modelos:
- **`nomic-embed-text`** — Para generar embeddings (representaciones vectoriales)
- **`qwen2.5-coder:3b`** — LLM (Modelo de lenguaje) para generar respuestas

Si no tienes Ollama instalado: https://ollama.ai

Verifica que esté corriendo antes de usar cualquier script.

---

## 📦 Paquetes Clave

| Paquete | Propósito |
|---------|-----------|
| `langchain-ollama` | Conectar con embeddings y LLM de Ollama |
| `langchain-community` | Loaders y vectorstore (Chroma) |
| `langchain-text-splitters` | Dividir documentos en chunks |
| `chromadb` | Base de datos vectorial local |
| `langchain-classic` | Chains y prompts (RetrievalQA) |

---

## 📁 Estructura de Directorios

```
.
├── src/                         # Código fuente (arquitectura modular)
│   ├── config.py               # Configuración centralizada
│   ├── rag/
│   │   ├── chain.py            # Lógica RAG (embeddings, vectorstore, LLM)
│   │   └── loader.py           # Carga documentos (.md, .txt, .py, .pdf)
│   ├── metrics/
│   │   ├── evaluator.py        # Evaluación de métricas
│   │   └── progress.py         # Visualización de progreso
│   └── utils/
│       ├── spinner.py          # Indicador de progreso
│       └── markdown_formatter.py # Formateador de respuestas
├── indexar.py                   # Entry point: indexación
├── consultar.py                 # Entry point: chat interactivo
├── evaluar.py                   # Entry point: evaluación
├── ver_progreso.py              # Entry point: visualizar métricas
├── docs/                        # Documentos fuente (a indexar)
├── chroma_db/                   # Base de datos vectorial (generada)
├── data/
│   └── metrics/                 # Métricas y evaluaciones (generado)
├── Pipfile                      # Dependencias del proyecto
└── README.md                    # Este archivo
```

---

## 🚀 Cómo Empezar

### 1. Activar el entorno virtual
```bash
pipenv shell
```

### 2. Instalar dependencias (primera vez)
```bash
pipenv install
```

### 3. Indexar documentos
Coloca tus documentos en `./docs/` y ejecuta:
```bash
pipenv run python indexar.py
```

### 4. Hacer consultas
```bash
pipenv run python consultar.py
```

Escribe tus preguntas en el REPL interactivo. Escribe `exit` para salir.

### 5. Evaluar métricas (opcional)
Para medir el rendimiento de tu RAG:
```bash
pipenv run python evaluar.py
```

---

## 📊 Sistema de Métricas

El proyecto incluye un sistema de evaluación para medir y trackear el rendimiento:

- **Relevancia**: Qué tan relevantes son los chunks recuperados
- **Calidad de respuestas**: Evaluación manual de respuestas
- **Latencia**: Tiempo de respuesta del sistema
- **Coverage**: Documentos que se utilizan en las respuestas

Las métricas se guardan en `./data/metrics/` para tracking histórico.

---

## 🔄 Flujo de Trabajo Típico

```
1. Agrega documentos → docs/
2. Ejecuta: pipenv run python indexar.py
3. Ejecuta: pipenv run python consultar.py
4. Haz preguntas y prueba respuestas
5. Ejecuta: pipenv run python evaluar.py
6. Revisa métricas en data/metrics/
7. Ajusta parámetros en src/config.py si es necesario
8. Repite
```

---

## 🎛️ Parámetros Ajustables

Puedes mejorar el rendimiento del RAG ajustando en `src/config.py`:

- **`RETRIEVER_K`**: Chunks recuperados. Actualmente 5. Prueba 3-10 según precisión deseada
- **`CHUNK_SIZE`**: Tamaño de chunks. Actualmente 800 tokens. Prueba 512-1024
- **`CHUNK_OVERLAP`**: Solapamiento. Actualmente 100 tokens. Prueba 50-200
- **Temperatura del LLM**: En `src/rag/chain.py`. Controla creatividad vs. determinismo (0.0-1.0)
- **`LLM_MODEL`**: Prueba modelos más grandes si recursos lo permiten

---

## 🏛️ Arquitectura del Código

El proyecto está organizado de forma modular y escalable:

- **`src/config.py`**: Configuración centralizada (ÚNICA fuente de verdad)
- **`src/rag/`**: Lógica RAG (carga documentos, construye chains)
- **`src/metrics/`**: Sistema de evaluación y visualización
- **`src/utils/`**: Utilidades (spinner, formateador de markdown)
- **Entry points** (`consultar.py`, `indexar.py`, etc.): Wrappers delgados que delegan a `src/`

Esto permite:
- ✅ Fácil reutilización de código
- ✅ Configuración centralizada (cambios en un solo lugar)
- ✅ Escalabilidad (agregar nuevos features sin duplicar lógica)
- ✅ Mantenimiento simplificado

---

## 📝 Notas

- **Requisito**: Ollama debe estar corriendo localmente
- **Privacidad**: Todo se procesa en tu máquina, sin datos en la nube
- **Velocidad**: La primera indexación puede ser lenta; consultas posteriores son rápidas
- **Modelos**: Los modelos se descargan automáticamente la primera vez que se usan
- **Refactor**: Código refactorizado a arquitectura modular (2026-04-19)

---

## 📚 Siguientes Pasos

- [ ] Interfaz web (FastAPI + UI)
- [ ] Mejor chunking (inteligente por estructura)
- [ ] Filtrado semántico (por etiquetas/tipo)
- [ ] Persistencia de historial
- [ ] Optimización de parámetros
- [ ] Testing automatizado

---

**Última actualización**: 2026-04-19 (refactor a arquitectura modular con `src/`)
