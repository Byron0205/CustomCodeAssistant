# 📊 Sistema de Métricas del RAG

Guía completa para evaluar y trackear el progreso de tu sistema RAG.

---

## 🎯 Propósito

El sistema de métricas permite:
- **Medir rendimiento** del RAG (latencia, calidad, relevancia)
- **Trackear progreso** a lo largo del tiempo
- **Identificar mejoras** mediante datos objetivos
- **Comparar ajustes** entre versiones diferentes

---

## 🚀 Cómo Empezar

### 1. Ejecutar evaluaciones
```bash
pipenv shell
pipenv run python evaluar.py
```

### 2. Ver progreso
```bash
pipenv run python ver_progreso.py
```

---

## 📝 Uso del Evaluador (`evaluar.py`)

### Opción 1: Preguntas Predefinidas
```
Opción (1-4): 1
```

Evalúa 5 preguntas base que ya vienen configuradas. Ideal para:
- Evaluaciones iniciales
- Comparar cambios en el RAG
- Crear baseline de métricas

**Preguntas incluidas:**
1. ¿Cuál es el propósito principal del proyecto?
2. ¿Qué modelos de Ollama se requieren?
3. ¿Cuál es el tamaño de los chunks de indexación?
4. ¿Qué directorios contiene la estructura del proyecto?
5. ¿Cuántos chunks se recuperan en cada consulta?

### Opción 2: Preguntas Personalizadas
```
Opción (1-4): 2
Pregunta: [Tu pregunta]
```

Permite evaluar cualquier pregunta arbitraria.

### Opción 3: Ver Estadísticas
```
Opción (1-4): 3
```

Muestra estadísticas agregadas de todas las evaluaciones.

---

## ⭐ Escala de Puntuación

Al calificar cada respuesta, usa esta escala:

### Calidad de Respuesta (1-5)
- **5** - Excelente: Respuesta completa, clara y precisa
- **4** - Buena: Respuesta correcta con información relevante
- **3** - Aceptable: Respuesta correcta pero incompleta o confusa
- **2** - Pobre: Respuesta con errores o poco relevante
- **1** - Muy pobre: Respuesta incorrecta o completamente irrelevante

### Relevancia (1-5)
- **5** - Altamente relevante: Todos los chunks utilizados son directamente relevantes
- **4** - Muy relevante: La mayoría de chunks son relevantes
- **3** - Relevante: Hay algunos chunks relevantes, otros menos
- **2** - Poco relevante: Pocos chunks relevantes
- **1** - No relevante: Chunks recuperados no ayudan a responder

---

## 📊 Uso del Visor de Progreso (`ver_progreso.py`)

### Resumen Ejecutivo (Opción 1)
Muestra:
- Total de evaluaciones realizadas
- Porcentaje de respuestas calificadas
- Promedio de calidad y relevancia
- Período de tiempo cubierto

**Ideal para:** Revisión rápida del estado general

### Últimas Evaluaciones (Opción 2)
Muestra las últimas 5 evaluaciones con:
- Pregunta evaluada
- Latencia
- Número de chunks
- Número de fuentes
- Calificaciones (si aplica)

**Ideal para:** Ver qué cambió recientemente

### Tendencia de Calidad (Opción 3)
Agrupa evaluaciones por semana y muestra:
- Promedio de calidad semanal
- Promedio de relevancia semanal
- Cambio neto (primera → última semana)

**Ideal para:** Identificar mejoras o degradaciones a largo plazo

### Análisis de Latencia (Opción 4)
Muestra:
- Latencia promedio
- Mínimo y máximo
- Desviación estándar
- Distribución por cuartiles (25%, 50%, 75%)

**Ideal para:** Monitorear velocidad del sistema

### Análisis de Cobertura (Opción 5)
Muestra:
- Total de documentos únicos encontrados
- Documentos más utilizados
- Promedio de chunks recuperados

**Ideal para:** Verificar que se usa la información correcta

---

## 🔄 Flujo de Trabajo Recomendado

### Semana 1: Baseline
```
1. Indexa tus documentos
2. Ejecuta: evaluar.py → Opción 1 (preguntas predefinidas)
3. Califica cada respuesta (calidad + relevancia)
4. Ejecuta: ver_progreso.py → Opción 1 (resumen)
```

**Resultado:** Tienes métricas iniciales para comparar.

### Semana 2: Ajustes
```
1. Modifica parámetros del RAG (chunk size, k, temperatura, etc.)
2. Re-indexa documentos si fue necesario
3. Ejecuta: evaluar.py → Opción 1 (mismas preguntas)
4. Califica nuevamente
5. Ejecuta: ver_progreso.py → Opción 3 (tendencias)
```

**Resultado:** Compara métricas vs. baseline. ¿Mejoraron?

### Cada Cambio Importante
```
Antes de cambiar:
  → evaluar.py (Opción 1) + calificar
  → Anotación en notas: "Baseline - chunk_size=800"

Después de cambiar:
  → evaluar.py (Opción 1) + calificar
  → Anotación en notas: "Después ajuste - chunk_size=1024"

Comparar resultados:
  → ver_progreso.py → Resumen o Tendencias
```

---

## 📁 Archivos de Datos

### `./metrics/evaluations.jsonl`
Archivo de líneas JSON. Cada línea es una evaluación:
```json
{
  "timestamp": "2026-04-14T15:30:45.123456",
  "question": "¿Cuál es el propósito principal del proyecto?",
  "response": "El propósito es...",
  "sources": ["README.md", "CLAUDE.md"],
  "num_sources": 2,
  "latency_seconds": 2.345,
  "chunks_retrieved": 5,
  "quality_score": 5,
  "relevance_score": 4,
  "notes": "Excelente, preciso"
}
```

**Por qué JSONL:** Permite append sin sobrescribir. Cada evaluación es una línea independiente.

### `./metrics/stats.json`
Resumen agregado generado por `ver_progreso.py`:
```json
{
  "total_evaluations": 15,
  "date_range": {
    "first": "2026-04-10T10:00:00",
    "last": "2026-04-14T15:30:45"
  },
  "latency": {
    "avg_seconds": 2.123,
    "min_seconds": 1.234,
    "max_seconds": 3.456
  },
  ...
}
```

---

## 🎯 Métricas Clave a Trackear

### 1. **Latencia**
- **Qué mide:** Velocidad de respuesta
- **Objetivo:** < 2 segundos idealmente
- **Cómo mejorar:** Menos chunks, modelos más rápidos, optimizar indexación

### 2. **Calidad Promedio**
- **Qué mide:** Qué tan buenas son las respuestas
- **Objetivo:** > 4.0 / 5.0
- **Cómo mejorar:** Mejor chunking, prompts más claros, mejores documentos

### 3. **Relevancia Promedio**
- **Qué mide:** Qué tan relevantes son los chunks recuperados
- **Objetivo:** > 4.0 / 5.0
- **Cómo mejorar:** Ajustar parámetros de búsqueda, mejorar embeddings, aumentar k

### 4. **Cobertura**
- **Qué mide:** Cuántos documentos distintos se utilizan
- **Objetivo:** Variadad (no siempre los mismos)
- **Cómo mejorar:** Mejor distribución de contenido, ajustes de similitud

---

## 💡 Tips y Mejores Prácticas

### 1. **Sé Consistente**
Usa las mismas preguntas predefinidas regularmente. Esto te permite comparar manzanas con manzanas.

### 2. **Anota Cambios**
Cada vez que hagas un ajuste, documenta en las "notas":
```
"Ajuste de k de 5 a 3 para reducir latencia"
"Chunk size aumentado de 800 a 1024"
"Modelo cambiado a qwen2.5-7b"
```

### 3. **Evaluación Periódica**
- **Semanal:** Ejecuta preguntas predefinidas (15 min)
- **Después de cada cambio:** Vuelve a evaluar (30 min)
- **Mensual:** Análisis profundo de tendencias (1 hora)

### 4. **Prueba Una Variable a la Vez**
No cambies múltiples parámetros simultáneamente. Así sabes qué causa el cambio.

### 5. **Documentación**
Mantén un registro de:
- Qué cambios hiciste
- Cuándo los hiciste
- Cómo afectaron las métricas

---

## 🐛 Troubleshooting

### "Error al cargar el RAG"
```
❌ Error al cargar el RAG: Connection error
⚠️  ¿Ollama está corriendo? ¿ChromaDB fue indexado?
```

**Solución:**
1. Verifica que Ollama esté corriendo: `ollama list`
2. Verifica que ChromaDB esté indexado: `pipenv run python indexar.py`

### No hay evaluaciones registradas
**Solución:** Ejecuta `evaluar.py` primero y califica algunas preguntas.

### Métricas raras o inconsistentes
**Verificación:**
- ¿Cambió el contenido de `./docs/`?
- ¿Reinstalaste ChromaDB?
- ¿Ollama se reinició?

Considera re-crear el baseline.

---

## 📈 Ejemplo de Progreso

Aquí hay un ejemplo típico de cómo las métricas evolucionan:

| Semana | Calidad | Relevancia | Latencia | Cambio |
|--------|---------|-----------|----------|--------|
| 1 (Baseline) | 3.2 | 3.1 | 3.5s | — |
| 2 | 3.5 | 3.4 | 3.2s | Ajustaste chunks |
| 3 | 4.1 | 3.9 | 2.8s | Mejor prompt |
| 4 | 4.3 | 4.2 | 2.5s | Optimización LLM |

**Conclusión:** Cada cambio pequeño se suma a mejoras mensurables.

---

## 🚀 Próximos Pasos

Después de recopilar datos:
- [ ] Identificar patrón de preguntas donde fallas
- [ ] Mejorar documentación en esas áreas
- [ ] Ajustar parámetros según patrones
- [ ] Re-evaluar y comparar

---

**Última actualización:** 2026-04-14
