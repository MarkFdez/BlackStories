# CONTEXT.md - Black Stories AI CLI Game

**Última Actualización:** 2025-12-18  
**Versión del Proyecto:** 0.1.0  
**Auditoría Realizada:** 2025-12-18

---

## 📋 Resumen del Proyecto

### Propósito
Black Stories AI CLI Game es una aplicación de terminal (CLI) que simula un juego de "Black Stories" (Historias Negras) utilizando modelos de lenguaje de inteligencia artificial. El sistema implementa una arquitectura de dos agentes:
- **Maestro (IA 1):** Crea el misterio, responde preguntas con "Sí/No/No relevante", y evalúa la solución final
- **Jugador (IA 2):** Intenta resolver el misterio mediante preguntas de pensamiento lateral

### Estado Actual
✅ **Funcional** - Implementación core completa con soporte multi-proveedor  
⚠️ **Grok Provider Incompleto** - Marcado como placeholder (ver Deuda Técnica)

### Stack Tecnológico

#### Lenguaje y Runtime
- **Python 3.x** (sin versión mínima especificada en pyproject.toml)
- **Gestor de Paquetes:** `uv` (recomendado)

#### Dependencias Principales
```toml
google-generativeai  # Google Gemini
openai               # OpenAI (GPT-3.5, GPT-4, etc.)
anthropic            # Anthropic (Claude)
ollama               # Ollama (modelos locales)
groq                 # Groq (no implementado)
rich                 # Terminal UI/Output
python-dotenv        # Variables de entorno
click                # CLI argument parsing
```

---

## 🏗️ Arquitectura del Sistema

### Patrón de Diseño
**Strategy Pattern + State Machine Hybrid**

- **Strategy Pattern:** Intercambio de proveedores de IA a través de `BaseProvider` (abstracción)
- **State Machine:** El Maestro opera en 3 fases (Generación → Interrogatorio → Evaluación)

### Estructura de Carpetas

```
BlackStories/
├── main.py                     # Entry point (CLI con Click)
├── game_manager.py             # Lógica principal del juego (State Machine)
├── saver.py                    # Persistencia (JSON/TXT/MD)
├── config.py                   # Carga de variables de entorno
├── pyproject.toml              # Configuración del proyecto
├── providers/                  # Implementaciones de AI Providers
│   ├── base_provider.py        # Clase abstracta (ABC)
│   ├── ollama_provider.py
│   ├── gemini_provider.py
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   └── grok_provider.py        # ⚠️ PLACEHOLDER (no funcional)
└── prompts/                    # System prompts por fase
    ├── maestro_fase1_gen.txt   # Fase 1: Generar JSON del misterio
    ├── maestro_fase2_juez.txt  # Fase 2: Responder Sí/No/No relevante
    ├── maestro_fase3_eval.txt  # Fase 3: Evaluar solución final
    └── jugador.txt             # Prompt del detective (estático)
```

### Responsabilidades de Componentes

#### `main.py` (Entry Point)
- **Responsabilidad:** Inicialización y configuración del juego
- **Funciones clave:**
  - `load_prompt(file_path)`: Carga un archivo de prompt individual
  - `load_all_prompts()`: Carga los 4 prompts desde `/prompts` por convención
  - `create_provider(provider_name, model_name, character_prompt)`: Factory para instanciar providers
  - `main()`: CLI entrypoint decorado con `@click.command()`

#### `game_manager.py` (Orquestación)
- **Responsabilidad:** Máquina de estados del juego, gestión de turnos, y parsing de respuestas
- **Clase:** `GameManager`
- **Métodos clave:**
  - `_initialize_story()`: Llama a Maestro con `TAREA: GENERAR`, parsea JSON, extrae `historia_secreta` y `acertijo_inicial`
  - `_get_master_response(question)`: Llama a Maestro con `TAREA: PREGUNTA`, valida respuesta Sí/No/No relevante (con reintentos)
  - `_handle_final_solution(solution)`: Llama a Maestro con `TAREA: EVALUAR`
  - `_parse_player_response(response_text)`: Extrae `<PENSAMIENTO>` y `<PREGUNTA>` del XML del Jugador
  - `start_game()`: Loop principal del juego (turnos, interacción, guardado)

#### `saver.py` (Persistencia)
- **Responsabilidad:** Guardado de historiales de partida
- **Formatos soportados:** JSON, TXT, Markdown (MD - por defecto)
- **Estructura del historial:**
  ```json
  {
    "metadata": {
      "master_provider": "...",
      "master_model": "...",
      "player_provider": "...",
      "player_model": "...",
      "master_prompt_gen": "...",
      "master_prompt_judge": "...",
      "master_prompt_eval": "...",
      "player_prompt": "...",
      "game_date": "ISO 8601"
    },
    "story": {
      "historia_secreta": "...",
      "acertijo_inicial": "..."
    },
    "conversation": [
      {"speaker": "player|master|master_final", "text": "...", "timestamp": "..."}
    ]
  }
  ```

#### `config.py` (Configuración)
- **Responsabilidad:** Carga de API keys desde `.env`
- **Variables esperadas:**
  - `GEMINI_API_KEY`
  - `OPENAI_API_KEY`
  - `ANTHROPIC_API_KEY`
  - `GROQ_API_KEY`

#### `providers/` (Strategy Pattern)
- **Base Abstracta:** `BaseProvider` (ABC)
  - Métodos obligatorios: `generate_response(prompt, system_prompt=None, **kwargs)`, `clear_history()`
- **Implementaciones:**
  - **OllamaProvider:** Usa librería `ollama`, sin autenticación
  - **GeminiProvider:** Usa `google.generativeai`, recrea cliente en cada llamada para system_prompt dinámico
  - **OpenAIProvider:** Usa `OpenAI` client, stateless
  - **AnthropicProvider:** Usa `anthropic.Anthropic`, `max_tokens=1024` hardcodeado
  - **GrokProvider:** ⚠️ Placeholder, devuelve respuesta dummy

---

## 🔄 Flujo de Datos

### Diagrama de Secuencia (Simplificado)

```
Usuario → CLI (main.py)
           ↓
       GameManager.start_game()
           ↓
     [FASE 1: GENERACIÓN]
       Maestro.generate_response("TAREA: GENERAR", system_prompt=maestro_fase1_gen.txt)
           → Devuelve JSON: {historia_secreta, acertijo_inicial}
           ↓
     [FASE 2: BUCLE DE INTERROGATORIO]
       Jugador.generate_response(historial) 
           → Devuelve XML: <PENSAMIENTO>...</PENSAMIENTO><PREGUNTA>...</PREGUNTA>
           ↓
       Maestro.generate_response("TAREA: PREGUNTA + historia_secreta + pregunta", system_prompt=maestro_fase2_juez.txt)
           → Devuelve "Sí" | "No" | "No relevante"
           ↓
       [Repetir hasta que Jugador.pregunta.startswith("Respuesta:")]
           ↓
     [FASE 3: EVALUACIÓN]
       Maestro.generate_response("TAREA: EVALUAR + historia_secreta + solución", system_prompt=maestro_fase3_eval.txt)
           → Devuelve evaluación final (texto libre)
           ↓
       saver.save_game(history, save_format)
```

### Puntos de Entrada
1. **CLI:** `python main.py -p1 <provider> -m1 <model> -p2 <provider> -m2 <model>`
2. **Carga de Prompts:** Desde archivos `.txt` en `prompts/` (convención fija)
3. **APIs Externas:** Gemini, OpenAI, Anthropic, Ollama (según provider seleccionado)

### Gestión de Estado
- **Sistema Stateless:** Cada llamada a `generate_response()` de los providers no mantiene historial interno
- **Historial Centralizado:** El `GameManager` construye el `conversation_history_for_player` como string acumulativo
- **Inyección de System Prompt:** El Maestro recibe un system_prompt diferente en cada fase (fase1_gen, fase2_juez, fase3_eval)

---

## 📐 Guía de Estilo y Convenciones

### Nombrado
- **Archivos:** `snake_case.py` (ej: `game_manager.py`, `openai_provider.py`)
- **Clases:** `PascalCase` (ej: `GameManager`, `BaseProvider`, `OpenAIProvider`)
- **Funciones/Métodos:** `snake_case` (ej: `load_prompt`, `start_game`, `_initialize_story`)
- **Métodos Privados:** Prefijo `_` (ej: `_get_master_response`, `_parse_player_response`)
- **Constantes Globales:** `UPPER_SNAKE_CASE` (ej: `PROVIDER_MAP`, `GEMINI_API_KEY`)

### Manejo de Errores
- **Validación de API Keys:** `ValueError` si la key no está configurada (en `__init__` de cada provider)
- **Errores de API:** Capturados con `try/except Exception`, devuelven mensaje de error como string (ej: `"Error: Could not get a response from OpenAI."`)
- **Interrupción del Usuario:** `KeyboardInterrupt` en el loop principal → guardado de progreso en bloque `finally`
- **Reintentos:** 
  - Generación de historia: 3 intentos (`_initialize_story`)
  - Validación de respuestas del Maestro: 3 intentos (`_get_master_response`)
  - Si falla, respuesta por defecto: `"No relevante"`

### Tipado
- **Sin Type Hints:** El proyecto NO usa anotaciones de tipo (Python sin typing)
- **Docstrings:** Presentes en funciones públicas y clases, estilo libre (sin seguir estrictamente Google/NumPy)

### Logging y Output
- **Libería:** `rich` (Console, Panel)
- **Convención de Colores:**
  - `[bold yellow]`: Advertencias, progreso del sistema
  - `[bold red]`: Errores críticos
  - `[bold green]`: Éxito (juego terminado)
  - `[bold magenta]`: Maestro
  - `[bold cyan]`: Jugador
  - `[italic grey50]`: Pensamiento del Jugador (opcional)
- **Sin Logging Formal:** No se usa `logging` module, solo `print` y `rich.console`

### Formato de Código
- **Indentación:** 4 espacios
- **Saltos de Línea:** CRLF (`\r\n` - Windows)
- **Comillas:** Comillas dobles `"` preferidas para strings
- **Imports:** Agrupados sin orden estricto (stdlib → third-party → local), sin separación visual

---

## 🗂️ Registro de Decisiones (Decision Log)

| Fecha       | Cambio Crítico | Justificación | Impacto |
|-------------|----------------|---------------|---------|
| *No hay registros previos a esta auditoría* | | | |

**Notas:**
- Este log se actualizará **solo** para cambios de lógica, arquitectura o API.
- Cambios de formato, typos o documentación NO se registran aquí.

---



### Mejoras Propuestas (No Bloqueantes)

1. **Logging Estructurado**
   - Reemplazar `print()` y `rich.console` con `logging` module
   - Permitir niveles de log configurables (`--verbose`)

2. **Configuración de Modelos**
   - Parámetros de temperatura, top_p, max_tokens como argumentos CLI opcionales
   - Actualmente todos los providers usan configuración por defecto

3. **Validación de System Prompts**
   - Verificar que los archivos `.txt` en `prompts/` contienen las etiquetas esperadas (`TAREA:`, `<PENSAMIENTO>`, etc.)

4. **Soporte para Streaming**
   - Los providers actuales esperan respuesta completa
   - Streaming mejoraría UX especialmente con modelos lentos

5. **Historial de Conversación Persistente**
   - Actualmente `conversation_history_for_player` es un string concatenado
   - Podría ser una lista estructurada para mejor parsing

---

## 📚 Documentación de Referencia

### Arquitectura de Prompts

#### Maestro (3 Fases)
1. **Fase 1 - Generación:** Recibe `"TAREA: GENERAR"`, devuelve JSON con `historia_secreta` y `acertijo_inicial`
2. **Fase 2 - Juez:** Recibe `"TAREA: PREGUNTA"` + historia + pregunta, devuelve una palabra: "Sí" | "No" | "No relevante"
3. **Fase 3 - Evaluación:** Recibe `"TAREA: EVALUAR"` + historia + solución, devuelve evaluación de texto libre

#### Jugador
- **Formato de Salida:** XML estructurado
  ```xml
  <PENSAMIENTO>
  [Análisis interno del detective]
  </PENSAMIENTO>
  <PREGUNTA>
  [Pregunta de Sí/No o solución final con "Respuesta:"]
  </PREGUNTA>
  ```

### Comandos de Uso

#### Ejecución Básica
```bash
python main.py \
    -p1 ollama -m1 llama3 \
    -p2 gemini -m2 gemini-1.5-pro \
    --save-format md
```

#### Parámetros CLI
- `-p1`, `--provider1`: Proveedor del Maestro (ollama|gemini|openai|anthropic|grok)
- `-m1`, `--model1`: Modelo del Maestro (ej: `llama3`, `gemini-1.5-pro`)
- `-p2`, `--provider2`: Proveedor del Jugador
- `-m2`, `--model2`: Modelo del Jugador
- `--save-format`: Formato de guardado (json|txt|md) - Default: `md`

**Nota:** Los parámetros `-c1` y `-c2` (character prompts) fueron removidos en refactor reciente. Ahora los prompts se cargan por convención desde `prompts/`.

---

## 🔐 Seguridad y Configuración

### Variables de Entorno Requeridas
Crear archivo `.env` en la raíz del proyecto:

```ini
GEMINI_API_KEY=tu_api_key
OPENAI_API_KEY=tu_api_key
ANTHROPIC_API_KEY=tu_api_key
GROQ_API_KEY=tu_api_key  # Opcional (provider no implementado)
```

### Archivos a Ignorar en Git
Ver `.gitignore` para lista completa. Críticos:
- `.env` (API keys)
- `blackstory_*.json|txt|md` (historiales de partida)

---

## ✅ Checklist de Onboarding

Para nuevos desarrolladores o agentes de IA:

1. ✅ Leer este `CONTEXT.md` completo
2. ✅ Revisar `README.md` para instrucciones de instalación
3. ✅ Configurar `.env` con al menos una API key válida
4. ✅ Ejecutar una partida de prueba con un proveedor disponible
5. ✅ Revisar el código de `game_manager.py` (corazón del sistema)
6. ✅ Entender el patrón Strategy en `providers/base_provider.py`
7. ✅ Leer los prompts en `prompts/` para entender la lógica del juego

---

**Fin del Documento** | Mantener este archivo actualizado es CRÍTICO para la coherencia del proyecto.
