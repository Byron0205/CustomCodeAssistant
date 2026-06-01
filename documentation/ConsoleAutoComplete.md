---
  # Autocompletado de comandos en el chat interactivo

  ## Cómo activarlo

  Presioná **Tab** en cualquier momento mientras escribís en el prompt `[default] >>`.

  ---

  ## Qué biblioteca lo implementa

  El autocompletado lo maneja **`prompt_toolkit`**, una librería de Python para construir interfaces de línea de comandos interactivas. Es la
  misma que usan herramientas como IPython y el REPL de Python.

  En el proyecto se usan tres componentes de `prompt_toolkit`:

  | Componente | Clase | Para qué sirve |
  |---|---|---|
  | Entrada interactiva | `prompt()` | Renderiza el campo de texto `[mode] >>` |
  | Autocompletado | `WordCompleter` | Define qué palabras se sugieren al presionar Tab |
  | Historial | `FileHistory` | Recuerda inputs anteriores (↑↓ entre sesiones) |

  ---

  ## Dónde está configurado (`consultar.py`)

  ### 1. La lista de palabras — `_completer`

  ```python
  from prompt_toolkit.completion import WordCompleter

  _completer = WordCompleter(
      [
          '/mode', '/modes', '/config', '/help', '/exit', '/salir',
          '/new', '/nuevo', '/chats', '/open', '/cargar',
          '/rename', '/delete', '/borrar', '/clear', '/limpiar',
          '/history', '/historial', '/reconnect', '/reconectar',
          *RAG_MODES.keys(),   # ← expande a: 'default', 'jira', 'refine'
      ],
      sentence=True,
  )

  WordCompleter recibe una lista plana de strings. Cada string es una palabra que puede sugerirse. El parámetro sentence=True le dice que
  opere sobre la última palabra del input, no sobre todo el texto — esto permite que /mode  + Tab ofrezca los nombres de modos.

  2. Inyección en el prompt — _read_input

  def _read_input(mode: str) -> str:
      return prompt(
          f'[{mode}] >> ',
          multiline=True,
          key_bindings=_kb,
          history=_history,
          completer=_completer,   # ← conecta el autocompletado al campo de texto
      )

  Al pasar completer=_completer a prompt(), la librería intercepta automáticamente la tecla Tab y muestra un menú de sugerencias filtrado por
  lo que ya escribiste.

  ---
  Comportamiento al presionar Tab

  WordCompleter con sentence=True trabaja así:

  1. Toma el texto que escribiste hasta el cursor.
  2. Identifica la última "palabra" (delimitada por espacios).
  3. Filtra la lista de palabras que empiecen con esa última palabra.
  4. Si hay una sola coincidencia: completa directamente.
  5. Si hay varias: muestra un menú desplegable. Podés navegar con ↑↓ y aceptar con Tab o Enter.

  Ejemplos concretos

  ┌─────────────────┬─────────────────────────────────────────────────┐
  │ Lo que escribís │                   Tab muestra                   │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /m              │ /mode, /modes                                   │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /mo             │ /mode, /modes                                   │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /mod            │ /mode, /modes                                   │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /mode           │ completa directo a /mode                        │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /mode           │ default, jira, refine                           │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /mode d         │ default                                         │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /h              │ /help, /history, /historial                     │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /re             │ /rename, /reconnect, /reconectar                │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ /c              │ /config, /chats, /cargar, /clear, /limpiar      │
  ├─────────────────┼─────────────────────────────────────────────────┤
  │ d (sin /)       │ default (también busca en los nombres de modos) │
  └─────────────────┴─────────────────────────────────────────────────┘

  ▎ Nota: el autocompletado no distingue entre comandos y nombres de modos en la misma lista — ambos están en _completer. Por eso escribir def
  ▎ + Tab también sugiere default. Esto es intencional: /mode def + Tab completa default sin tener que escribirlo entero.

  ---
  Por qué sentence=True

  Sin sentence=True, WordCompleter completaría la primera palabra del input — útil para un solo comando por línea, pero en este proyecto /mode
  default tiene dos palabras. Con sentence=True el completer trabaja sobre la última palabra, lo que habilita el flujo:

  /mode [Tab]   →   sugiere: default, jira, refine
  /mode d[Tab]  →   completa: default

  ---
  Cómo agregar un comando nuevo al autocompletado

  Solo hay que agregar el string a la lista en _completer dentro de consultar.py:

  _completer = WordCompleter(
      [
          ...
          '/mi-nuevo-comando',   # ← agregar acá
          *RAG_MODES.keys(),
      ],
      sentence=True,
  )

  Si el comando tiene un argumento (como /mode <nombre>), también agregar los valores posibles del argumento a la misma lista — WordCompleter
  los ofrecerá después del espacio.

  ---
  Cómo agregar un modo nuevo

  Los modos se agregan en src/config.py dentro del dict RAG_MODES. El autocompletado los recoge automáticamente gracias al *RAG_MODES.keys():

  # src/config.py
  RAG_MODES = {
      "default": { ... },
      "jira":    { ... },
      "refine":  { ... },
      "mi-modo": { ... },   # ← al agregar esto, Tab ya lo sugiere
  }

  No hay que tocar consultar.py para que aparezca en el autocompletado.

  ---
  Historial de inputs (↑ ↓)

  El historial es independiente del autocompletado. Lo maneja FileHistory:

  from prompt_toolkit.history import FileHistory

  _history = FileHistory(str(DATA_DIR / '.rag_history'))
  # guarda en: data/.rag_history

  Cada línea que enviás (comandos y preguntas) se guarda en ese archivo. Al presionar ↑ navegás hacia atrás en el historial, incluso entre
  sesiones distintas del proyecto. El archivo es texto plano — podés inspeccionarlo o borrarlo si querés limpiar el historial.
  ```