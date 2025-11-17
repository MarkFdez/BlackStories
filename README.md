# Black Stories AI CLI Game

Esta es una aplicación de terminal (CLI) que simula un juego de "Black Stories" (Historias Negras) utilizando modelos de lenguaje de inteligencia artificial. Un modelo actúa como el "Maestro" del juego, creando un misterio, mientras que un segundo modelo actúa como el "Jugador", intentando resolverlo a través de preguntas.

## Flujo del Juego

1.  El **Maestro (IA 1)** genera una historia de misterio secreta y presenta un acertijo inicial.
2.  El **Jugador (IA 2)** recibe el acertijo y debe hacer preguntas para resolver el misterio.
3.  El **Maestro** solo puede responder a estas preguntas con "Sí", "No" o "No relevante".
4.  El ciclo de preguntas y respuestas continúa hasta que el Jugador cree haber resuelto el misterio.
5.  El Jugador presenta su solución final, y el Maestro la evalúa, revelando finalmente la historia secreta completa.

## Características

*   **Multi-Proveedor de IA:** Soporta múltiples proveedores de modelos como Ollama, Google Gemini, OpenAI, Anthropic y Groq.
*   **Personalidades Configurables:** Permite definir la personalidad y las instrucciones de cada IA a través de archivos de texto.
*   **Visualización Clara:** Utiliza la librería `rich` para una salida en terminal colorida y bien estructurada.
*   **Juego Interactivo:** Pausa después de cada turno, esperando la intervención del usuario para continuar.
*   **Guardado Automático:** Guarda un registro completo de cada partida, incluyendo la historia secreta, los prompts y toda la conversación.
*   **Manejo de Errores:** Robusto ante errores de API, archivos no encontrados y finalización abrupta (`Ctrl+C`).

## Instalación

Se recomienda el uso de `uv` como gestor de paquetes y entorno virtual.

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/your-username/black-stories-ai.git
    cd black-stories-ai
    ```

2.  **Crear un entorno virtual e instalar dependencias con `uv`:**
    ```bash
    uv venv
    uv pip install -r requirements.txt 
    # O directamente desde el pyproject.toml
    uv pip install .
    ```
    *Nota: Si no tienes `requirements.txt`, `uv` leerá las dependencias del `pyproject.toml`.*

3.  **Configurar las claves de API:**
    *   Renombra el archivo `.env.example` a `.env`.
    *   Abre el archivo `.env` y añade tus claves de API para los proveedores que desees utilizar.

    ```ini
    # .env
    GEMINI_API_KEY="TU_API_KEY_DE_GEMINI"
    OPENAI_API_KEY="TU_API_KEY_DE_OPENAI"
    ANTHROPIC_API_KEY="TU_API_KEY_DE_ANTHROPIC"
    GROQ_API_KEY="TU_API_KEY_DE_GROQ"
    ```

## Uso

La aplicación se ejecuta desde la línea de comandos, proporcionando los modelos y los archivos de personalidad para el Maestro y el Jugador.

### Parámetros de la CLI

*   `-p1`, `--provider1`: **(Obligatorio)** Proveedor del Maestro (`ollama`, `gemini`, `openai`, `anthropic`, `grok`).
*   `-m1`, `--model1`: **(Obligatorio)** Modelo del Maestro (ej: `llama3`, `gemini-1.5-pro`).
*   `-c1`, `--character1`: **(Obligatorio)** Ruta al archivo de prompt del Maestro.
*   `-p2`, `--provider2`: **(Obligatorio)** Proveedor del Jugador.
*   `-m2`, `--model2`: **(Obligatorio)** Modelo del Jugador.
*   `-c2`, `--character2`: **(Obligatorio)** Ruta al archivo de prompt del Jugador.
*   `--save-format`: Formato de guardado (`json`, `txt`, `md`). Por defecto: `md`.

### Ejemplo de Ejecución

```bash
python main.py \
    -p1 ollama -m1 llama3 -c1 prompts/maestro_prompt.txt \
    -p2 gemini -m2 gemini-1.5-pro -c2 prompts/jugador_prompt.txt \
    --save-format json
```

## Ejemplos de Archivos de Personalidad

El éxito del juego depende en gran medida de la calidad de los prompts.

### `maestro_prompt.txt`

```text
Eres el Maestro de un juego de Black Stories. Tu rol tiene varias fases.

FASE 1: CREACIÓN DEL MISTERIO
Cuando te contacten por primera vez, debes generar internamente una historia de misterio completa sobre una muerte en circunstancias extrañas. A partir de esa historia, crea un acertijo inicial. Tu respuesta DEBE ser únicamente un objeto JSON válido y nada más. No incluyas texto antes o después del JSON. El JSON debe tener esta estructura estricta:
{
  "historia_secreta": "La historia completa y detallada del misterio.",
  "acertijo_inicial": "Una o dos frases que sirvan como punto de partida para el jugador."
}

FASE 2: RESPONDER PREGUNTAS
Después de la fase 1, un jugador intentará resolver el misterio haciéndote preguntas. Para cada pregunta, debes compararla con tu "historia_secreta". Tu respuesta DEBE ser, estricta y exclusivamente, una de las siguientes tres opciones: "Sí", "No", o "No relevante". No añadas ninguna explicación.

FASE 3: EVALUACIÓN FINAL
Cuando el jugador te presente una solución final (que comenzará con "Respuesta:"), evalúala comparándola con tu "historia_secreta". Anuncia si la solución es correcta o incorrecta y, a continuación, revela la "historia_secreta" completa.
```

### `jugador_prompt.txt`

```text
Eres un detective brillante intentando resolver un misterio. Te darán un acertijo inicial. Tu objetivo es descubrir la historia completa detrás del acertijo.

REGLAS:
1. Solo puedes hacer preguntas que puedan ser respondidas con "Sí", "No" o "No relevante".
2. Analiza las respuestas para formular tu siguiente pregunta.
3. Cuando creas que has resuelto el misterio, presenta tu solución final comenzando con el prefijo "Respuesta:". Por ejemplo: "Respuesta: El hombre era un payaso sobre zancos que resbaló con una cáscara de plátano.".
