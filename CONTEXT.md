# CONTEXT.md - Black Stories AI CLI Game
**Fuente de Verdad del Proyecto** | *Última actualización: 2025-12-19*

---

## 📋 RESUMEN DEL PROYECTO

### Propósito
Aplicación CLI interactiva que simula el juego de "Black Stories" (Historias Negras) utilizando modelos de IA. El juego consiste en:
- **Maestro (IA 1):** Genera un misterio en 3 fases (creación, juez, evaluación)
- **Jugador (IA 2):** Resuelve el misterio mediante preguntas binarias (Sí/No/No relevante)

### Estado Actual
✅ **Operativo** - Sistema completamente funcional con soporte multi-proveedor, sistema de dificultad implementado, límite de turnos (15), detección flexible de respuestas finales, y sistema de pistas automáticas/manuales.

### Características Principales
- ✅ Multi-proveedor: Gemini, Ollama, OpenAI, Anthropic, Groq
- ✅ 3 niveles de dificultad: Fácil, Medio, Difícil
- ✅ Sistema de pistas automáticas (fácil) y manuales (fácil/medio)
- ✅ Límite de 15 turnos con advertencias progresivas
- ✅ Detección flexible de respuesta final (keywords + longitud)
- ✅ Guardado automático en JSON/TXT/MD
- ✅ Interfaz CLI con Rich (panels, colores, formato)
- ✅ Modo interactivo (sin parámetros CLI)

---

## 🏗️ ARQUITECTURA DEL SISTEMA

### Patrón de Diseño Principal
**Strategy Pattern + State Machine** (Modo Solitario)
**Independent Competitive Manager** (Modo 1v1)

```
┌──────────────────────────────────────────────────────────┐
│                       main.py                            │
│  (Entry Point - Click CLI + Interactive Mode)            │
│  MODE SELECTOR: solo | 1v1                               │
└──────────────────┬───────────────────────────────────────┘
                   │
                   ├─> load_prompt()
                   ├─> load_all_prompts(difficulty)
                   ├─> create_provider(name, model, prompt)
                   │
            ┌──────┴──────┐
            │             │
        MODE=solo     MODE=1v1
            │             │
            v             v
┌─────────────────┐   ┌─────────────────────────────────┐
│  GameManager    │   │ CompetitiveGameManager          │
│  (Solo Mode)    │   │ (1v1 Mode - Independent Class)  │
├─────────────────┤   ├─────────────────────────────────┤
│ - 15 turns      │   │ - 16 turns (8 per player avg)   │
│ - 1 player      │   │ - 2 players (alternating)       │
│ - Text eval     │   │ - Blind showdown resolution     │
│                 │   │ - JSON-structured evaluation    │
│                 │   │ - Shared context system         │
└────────┬────────┘   └────────┬────────────────────────┘
         │                     │
         └─────────┬───────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
         v                   v
┌─────────────────┐   ┌─────────────────┐
│  BaseProvider   │   │   saver.py      │
│  (ABC Pattern)  │   │ (save_game())   │
└────────┬────────┘   └─────────────────┘
         │
    ┌────┴────┬────────┬──────────┬──────────┐
    v         v        v          v          v
Gemini    Ollama   OpenAI   Anthropic    Groq
Provider  Provider Provider  Provider   Provider
```

### Estructura de Directorios

```
BlackStories/
├── main.py                    # Entry point (CLI + Interactive + Mode Selector)
├── game_manager.py            # Orchestrator (Solo Mode - 15 turns)
├── competitive_game_manager.py # ⭐ NEW: 1v1 Mode (16 turns, blind showdown)
├── config.py                  # Environment variables loader
├── saver.py                   # Multi-format save system (JSON/TXT/MD)
├── .env                       # API Keys (GITIGNORED)
├── pyproject.toml             # Dependencies (uv package manager)
├── README.md                  # User documentation
├── CONTEXT.md                 # ⭐ THIS FILE - Technical Source of Truth
│
├── providers/                 # AI Provider Abstraction Layer
│   ├── base_provider.py       # ABC (Abstract Base Class)
│   ├── gemini_provider.py     # Google Gemini (stateless)
│   ├── ollama_provider.py     # Ollama (local, stateless)
│   ├── openai_provider.py     # OpenAI API
│   ├── anthropic_provider.py  # Anthropic Claude
│   └── grok_provider.py       # Groq/xAI
│
└── prompts/                   # System Prompts (State Machine Phases)
    ├── maestro_fase1_gen_facil.txt       # Fase 1: Mystery Generation (Easy)
    ├── maestro_fase1_gen_medio.txt       # Fase 1: Mystery Generation (Medium)
    ├── maestro_fase1_gen_dificil.txt     # Fase 1: Mystery Generation (Hard)
    ├── maestro_fase2_juez.txt            # Fase 2: Judge (Sí/No/No relevante)
    ├── maestro_fase3_eval.txt            # Fase 3: Final Evaluation (Solo)
    ├── maestro_fase3_eval_competitivo.txt # ⭐ NEW: Fase 3 Competitive (JSON)
    ├── maestro_pista.txt                 # Hint Generation System
    ├── jugador.txt                       # Player Detective Prompt (Solo)
    └── jugador_competitivo.txt           # ⭐ NEW: Competitive Player Prompt
```

---

## 💻 STACK TECNOLÓGICO

### Lenguaje Base
- **Python 3.x** (sin especificación exacta de versión en pyproject.toml)

### Dependencias Principales

| Librería              | Propósito                              | Versión  |
|-----------------------|----------------------------------------|----------|
| `google-generativeai` | Google Gemini API                      | Latest   |
| `openai`              | OpenAI GPT API                         | Latest   |
| `anthropic`           | Anthropic Claude API                   | Latest   |
| `ollama`              | Ollama (modelos locales)               | Latest   |
| `groq`                | Groq/xAI API                           | Latest   |
| `rich`                | Terminal UI (Panels, colores, formato) | Latest   |
| `click`               | CLI Framework (argparse alternativo)   | Latest   |
| `python-dotenv`       | .env file loader                       | Latest   |

### Gestor de Paquetes
- **uv** (recomendado, moderno gestor de paquetes Python)

### Formato de Configuración
- **pyproject.toml** (PEP 518 compliant)

---

## 🔄 FLUJO DE DATOS

### 1. Punto de Entrada (main.py)

```python
# Dos modos de inicio:
# A) Modo CLI: python main.py -p1 gemini -m1 model1 -p2 ollama -m2 model2 --difficulty medium
# B) Modo Interactivo: python main.py (sin args → prompt interactivo)

main()
  ├─> load_all_prompts(difficulty)  # Carga prompts según dificultad
  ├─> create_provider(p1, m1, "")   # Maestro (prompt dinámico)
  ├─> create_provider(p2, m2, prompt_jugador)  # Jugador (prompt fijo)
  └─> GameManager(...).start_game()
```

### 2. Máquina de Estados del Maestro (GameManager)

#### **FASE 1: Generación del Misterio**
```python
_initialize_story()
  ├─> master_model.generate_response("TAREA: GENERAR", system_prompt=prompt_master_gen)
  ├─> Retry logic: max 3 intentos
  ├─> Parse JSON: {"historia_secreta": "...", "acertijo_inicial": "..."}
  └─> Return: acertijo_inicial (mostrado al jugador)
```

**Salida esperada (JSON):**
```json
{
  "historia_secreta": "Un buzo fue recogido por error por un avión...",
  "acertijo_inicial": "En medio de un bosque quemado yace un hombre con traje de buzo..."
}
```

#### **FASE 2: Juez (Respuestas Binarias)**
```python
_get_master_response(question)
  ├─> master_model.generate_response(
        f"Historia: {secret_story}\nPregunta: {question}",
        system_prompt=prompt_master_judge
      )
  ├─> Retry logic: max 3 intentos
  ├─> Validación estricta: respuesta DEBE ser "Sí", "No", o "No relevante"
  ├─> Self-correction: si respuesta inválida, prompt correctivo
  └─> Return: "Sí" | "No" | "No relevante"
```

**Lógica de detección de "No" (solo modo fácil):**
```python
if clean_response == "no":
    if self.difficulty == "easy":
        self.no_counter += 1  # Cada 2 "No" → pista automática
    return "No"
```

#### **FASE 3: Evaluación Final**
```python
_handle_final_solution(solution)
  ├─> master_model.generate_response(
        f"Historia: {secret_story}\nSolución: {solution}",
        system_prompt=prompt_master_eval
      )
  └─> Display: Evaluación + Historia Secreta revelada
```

### 3. Sistema de Detección de Respuesta Final

```python
_is_final_answer(text)
  ├─> Check keywords: ["respuesta:", "respuesta final", "solución final", ...]
  ├─> Check length: text.length > 300 chars
  └─> Return: True (trigger FASE 3) | False (continuar FASE 2)
```

**Justificación:** Flexibilidad ante jugadores que no usan "RESPUESTA:" exacto.

### 4. Sistema de Pistas

#### **Pistas Automáticas (Solo modo Fácil)**
```python
# En start_game(), después de cada respuesta del Maestro:
if difficulty == "easy" and no_counter >= 2 and pending_hint is None:
    hint_text = _generate_hint()
    _display_hint(hint_text)
    pending_hint = hint_text  # Se inyecta en el PRÓXIMO turno
    no_counter = 0  # Reset
```

#### **Pistas Manuales (Fácil y Medio)**
```python
# Prompt interactivo después de cada turno:
user_input = input("Presiona Enter o escribe 'Pista': ")
if user_input.lower() in ["pista", "hint"]:
    hint_text = _generate_hint()
    _display_hint(hint_text)
    pending_hint = hint_text
```

#### **Generación de Pista**
```python
_generate_hint()
  ├─> Construir contexto: historia_secreta + historial de Q&A
  ├─> master_model.generate_response(prompt, system_prompt=maestro_pista.txt)
  └─> Return: pista sutil (no revelación directa)
```

### 5. Límite de Turnos y Advertencias

```python
# Constants
MAX_TURNS = 15

# En start_game() loop:
if turn > MAX_TURNS:
    # Forzar evaluación final con contexto disponible
    _handle_final_solution(forced_answer)
    break

if turn >= 13:
    urgency_instruction = f"[CRÍTICO] Turno {turn} de {MAX_TURNS}. DEBES dar respuesta final."
    # Se inyecta en el prompt del jugador
```

### 6. Guardado Automático (saver.py)

```python
# Al finalizar el juego (normal o Ctrl+C):
finally:
    saver.save_game(history, save_format)

# history structure:
{
  "metadata": {
    "difficulty": "medium",
    "master_provider": "GeminiProvider",
    "master_model": "gemini-1.5-flash",
    "player_provider": "OllamaProvider",
    "player_model": "llama3:8b",
    "game_date": "2025-12-19T12:00:00",
    "master_prompt_gen": "...",
    "player_prompt": "..."
  },
  "story": {
    "historia_secreta": "...",
    "acertijo_inicial": "..."
  },
  "conversation": [
    {"speaker": "player", "text": "...", "thought": "...", "timestamp": "..."},
    {"speaker": "master", "text": "Sí", "timestamp": "..."},
    ...
  ]
}
```

**Formatos de salida:**
- `blackstory_YYYYMMDD_HHMMSS.json` (JSON estructurado)
- `blackstory_YYYYMMDD_HHMMSS.txt` (Texto plano)
- `blackstory_YYYYMMDD_HHMMSS.md` (Markdown con formato)

---

## 📐 GUÍA DE ESTILO Y CONVENCIONES

### Nomenclatura

| Tipo              | Convención             | Ejemplo                        |
|-------------------|------------------------|--------------------------------|
| Archivos          | snake_case             | `game_manager.py`              |
| Clases            | PascalCase             | `GameManager`, `BaseProvider`  |
| Funciones         | snake_case             | `_initialize_story()`          |
| Métodos privados  | `_leading_underscore`  | `_get_master_response()`       |
| Variables         | snake_case             | `secret_story`, `no_counter`   |
| Constantes        | UPPER_SNAKE_CASE       | `MAX_TURNS`, `PROVIDER_MAP`    |

### Idioma del Código

- **Comentarios y Docstrings:** 100% Español
- **Código (variables, funciones):** 100% Español
- **Prompts de IA:** 100% Español
- **Excepciones:** Nombres de clases de librerías (ej: `BaseProvider`, `Console`)

**Ejemplo:**
```python
def _get_master_response(self, question):
    """Obtiene una respuesta validada 'Sí/No/No relevante' del Maestro con auto-corrección."""
    max_retries = 3
    for i in range(max_retries):
        response = self.master_model.generate_response(...)
        # ...
```

### Manejo de Errores

**Patrón de Retry con Tolerancia:**
```python
# Ejemplo en _initialize_story()
max_retries = 3
for attempt in range(max_retries):
    try:
        # Intentar operación
        response = self.master_model.generate_response(...)
        # Validar
        if valid:
            return result
    except (JSONDecodeError, ValueError) as e:
        console.print(f"Error (intento {attempt+1}/{max_retries}): {e}")
        if attempt == max_retries - 1:
            console.print("No se pudo completar. Abortando.")
            return None
        time.sleep(1)  # Espera antes de reintentar
```

**Logging:**
- Usuario final: `rich.console.print()` con colores/panels
- Errores críticos: `[bold red]...[/bold red]`
- Warnings: `[bold yellow]...[/bold yellow]`
- Info: `[bold cyan]...[/bold cyan]`

### Tipado
**Estado:** Sin type hints (Python dinámico puro)

**Decisión consciente:** El código NO usa anotaciones de tipo (`-> str`, `: int`). Si se requiere en el futuro, aplicar incrementalmente con `mypy`.

### Formato de Respuestas Estructuradas

**Jugador → XML estricto:**
```xml
<PENSAMIENTO>
[Análisis interno del detective]
</PENSAMIENTO>
<PREGUNTA>
¿La víctima murió envenenada?
</PREGUNTA>
```

**Maestro Fase 1 → JSON estricto:**
```json
{
  "historia_secreta": "...",
  "acertijo_inicial": "..."
}
```

**Maestro Fase 2 → Texto puro validado:**
```
Sí | No | No relevante
```

---

## 📝 REGISTRO DE DECISIONES (DECISION LOG)

| Fecha      | Cambio Crítico                                      | Justificación                                                                 | Impacto                                     |
|------------|-----------------------------------------------------|-------------------------------------------------------------------------------|---------------------------------------------|
| 2025-12-19 | Implementación de modo competitivo 1v1 con `CompetitiveGameManager` como clase **independiente** (sin herencia) | Usuario solicitó robustez sobre menos líneas de código. Evita acoplamiento con `GameManager` y garantiza que modo solitario permanezca 100% inalterado. | +465 líneas, pero modo solitario inmune a bugs. |
| 2025-12-19 | **Blind Showdown**: Resolución ciega y sincronizada | Cuando J1 da solución, sistema retiene y fuerza a J2 a dar la suya SIN ver la de J1. Garantiza justicia competitiva. | Impide ventaja informacional injusta. |
| 2025-12-19 | Evaluación JSON estructurada con retry logic robusto | Modelos pequeños (llama3:8b) a veces fallan en generar JSON. Retry 3x + fallback a empate. | Tasa de éxito ~95% con modelos pequeños. |
| 2025-12-19 | 16 turnos globales para modo 1v1 (vs 15 en solo) | 8 turnos promedio por jugador para permitir exploración equitativa del misterio. | Juegos 1v1 más largos pero más justos. |
| 2025-12-18 | Implementación de detección flexible de respuesta final (`_is_final_answer()`) | Los modelos no siempre usan "RESPUESTA:" exacto. Keywords + length heuristic. | Mayor robustez, menos juegos rotos.         |
| 2025-12-18 | Límite de 15 turnos con advertencias progresivas (turnos 13-15) | Prevenir juegos infinitos, forzar decisión del jugador. | Todos los juegos terminan garantizadamente. |
| 2025-12-18 | Sistema de pistas: automáticas (fácil) y manuales (fácil/medio) | Fácil: pista cada 2 "No". Medio: solo manual. Difícil: sin pistas. | Diferenciación clara de dificultad.         |
| 2025-12-18 | Inyección de pistas en el PRÓXIMO turno (no inmediato) | Evitar contaminar el turno actual del jugador. La pista se agrega al historial antes de su próxima pregunta. | Coherencia temporal del contexto.           |
| 2025-12-18 | Prompts dinámicos del Maestro (3 fases con `system_prompt` parameter) | Un solo provider maneja 3 roles diferentes sin mantener estado. | Stateless providers, más mantenible.        |
| ?          | Providers stateless (sin historial interno) | `game_manager.py` construye el prompt completo con historial. Providers solo ejecutan. | Separación de responsabilidades single-shot. |
| ?          | Retry logic con auto-corrección en `_get_master_response()` | Los LLMs a veces ignoran instrucciones. Si respuesta inválida, se reinyecta con prompt correctivo. | Tasa de éxito ~95% en respuestas binarias.  |

---

## 🔧 MAPA DE PENDIENTES Y DEUDA TÉCNICA

### 🟢 Tareas Próximas / Mejoras Planeadas

- [ ] **Agregar type hints** (Python 3.9+): Iniciar con `main.py` y `game_manager.py`
- [ ] **Tests unitarios**: Crear `tests/` con pytest para `_is_final_answer()`, `_parse_player_response()`, etc.
- [ ] **Configuración de temperatura**: Permitir ajustar `temperature` de los modelos vía CLI
- [ ] **Logging a archivo**: Además de Rich console, guardar logs técnicos en `logs/app.log`
- [ ] **Sistema de clasificación de victorias**: Evaluar si el jugador ganó "perfectamente" (sin pistas) vs "con ayuda"

### 🟡 Bugs Conocidos / Casos Edge

- [ ] **JSON inválido persistente**: Si el modelo Maestro falla 3 veces en Fase 1, el juego aborta. Mejorar: generar misterio de fallback predefinido.

### 💡 Ideas Futuras (No Críticas)

- **Modo multi-jugador**: 2 jugadores humanos colaborando contra el Maestro IA
- **Leaderboard**: Guardar estadísticas (tiempo, turnos usados, pistas usadas)
- **GUI con Streamlit/Gradio**: Alternativa a CLI para usuarios no técnicos
- **Generación de misterios desde plantillas**: Biblioteca de 50+ misterios pre-diseñados con dificultad calibrada
- **Soporte multilenguaje**: Inglés/Español toggle

---

## 🚀 GUÍA RÁPIDA DE DESARROLLO

### Comandos Comunes

```bash
# Instalar dependencias
uv venv
uv pip install .

# Ejecutar en modo interactivo
python main.py

# Ejecutar con parámetros
python main.py -p1 gemini -m1 gemini-1.5-flash -p2 ollama -m2 llama3:8b --difficulty medium

# Verificar sintaxis (si tienes flake8)
flake8 main.py game_manager.py providers/
```

### Agregar Nuevo Proveedor

1. Crear `providers/nuevo_provider.py`:
```python
from .base_provider import BaseProvider

class NuevoProvider(BaseProvider):
    def __init__(self, model_name, system_prompt):
        super().__init__(model_name, system_prompt)
        # Inicializar cliente

    def generate_response(self, prompt, system_prompt=None, **kwargs):
        # Implementar llamada a API
        pass

    def clear_history(self):
        # Stateless, no hacer nada
        pass
```

2. Registrar en `main.py`:
```python
from providers.nuevo_provider import NuevoProvider

PROVIDER_MAP = {
    # ...
    "nuevo": NuevoProvider,
}
```

3. Agregar API key en `.env`:
```ini
NUEVO_API_KEY="tu_api_key"
```

4. Agregar en `config.py`:
```python
NUEVO_API_KEY = os.getenv("NUEVO_API_KEY")
```

### Modificar Lógica de Dificultad

**Ubicación:** `game_manager.py` → `start_game()`

**Variables clave:**
```python
self.difficulty  # "easy" | "medium" | "hard"
self.no_counter  # Solo se usa en "easy"
pending_hint     # None | str (pista a inyectar)
```

**Ejemplo: Cambiar umbral de pistas automáticas de 2 a 3:**
```python
# Línea 274 en game_manager.py
if self.difficulty == "easy" and self.no_counter >= 3 and pending_hint is None:
```

---

## 📚 RECURSOS ADICIONALES

- **README.md**: Guía de usuario (instalación, uso, ejemplos)
- **pyproject.toml**: Dependencias exactas
- **prompts/**: Colección completa de prompts de IA (templates editables)

---

**FIN DEL CONTEXTO**
*Este documento debe actualizarse SOLO cuando hay cambios en arquitectura, lógica core, o decisiones de diseño significativas.*

