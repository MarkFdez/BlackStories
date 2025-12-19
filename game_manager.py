import json
import time
import re
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
import saver

class GameManager:
    def __init__(self, master_model, player_model, save_format="md", difficulty="medium",
                 prompt_master_gen="", prompt_master_judge="", prompt_master_eval=""):
        self.master_model = master_model
        self.player_model = player_model
        self.save_format = save_format
        self.difficulty = difficulty
        self.no_counter = 0  # Contador de respuestas "No" (solo para modo fácil)
        self.console = Console()
        self.secret_story = ""
        
        # Store phase-specific prompts
        self.prompt_master_gen = prompt_master_gen
        self.prompt_master_judge = prompt_master_judge
        self.prompt_master_eval = prompt_master_eval

        self.history = {
            "metadata": {
                "difficulty": difficulty,
                "master_provider": master_model.__class__.__name__,
                "master_model": master_model.model_name,
                "player_provider": player_model.__class__.__name__,
                "player_model": player_model.model_name,
                "master_prompt_gen": self.prompt_master_gen,
                "master_prompt_judge": self.prompt_master_judge,
                "master_prompt_eval": self.prompt_master_eval,
                "player_prompt": player_model.system_prompt,
                "game_date": datetime.now().isoformat(),
            },
            "story": {},
            "conversation": []
        }

    def _initialize_story(self):
        """Calls the Master model to get the initial mystery in JSON format."""
        self.console.print(Panel("[bold yellow]El Maestro está creando un nuevo misterio...[/bold yellow]", border_style="yellow"))
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                initial_prompt = "TAREA: GENERAR"
                response_text = self.master_model.generate_response(
                    initial_prompt, 
                    system_prompt=self.prompt_master_gen
                )
                
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start == -1 or json_end == 0:
                    raise json.JSONDecodeError("No JSON object found in the response.", response_text, 0)
                
                json_str = response_text[json_start:json_end]
                story_data = json.loads(json_str)

                if "historia_secreta" in story_data and "acertijo_inicial" in story_data:
                    self.secret_story = story_data["historia_secreta"]
                    self.history["story"] = story_data
                    self.master_model.clear_history()
                    return story_data["acertijo_inicial"]
                else:
                    raise ValueError("El JSON recibido no tiene las claves 'historia_secreta' o 'acertijo_inicial'.")

            except (json.JSONDecodeError, ValueError) as e:
                self.console.print(f"[bold red]Error al parsear el misterio del Maestro (intento {attempt + 1}/{max_retries}): {e}[/bold red]")
                if attempt == max_retries - 1:
                    self.console.print("[bold red]No se pudo iniciar el juego. El Maestro no proporcionó un JSON válido.[/bold red]")
                    return None
                time.sleep(1)
        return None

    def _get_master_response(self, question):
        """Gets a validated 'Sí/No/No relevante' response from the Master with self-correction."""
        self.master_model.clear_history()
        prompt = f"TAREA: PREGUNTA\n\n---\nHistoria Secreta: \"{self.secret_story}\"\n---\nPregunta del Jugador: \"{question}\""
        
        max_retries = 3
        for i in range(max_retries):
            response = self.master_model.generate_response(
                prompt, 
                system_prompt=self.prompt_master_judge
            ).strip()
            clean_response = response.replace("*", "").replace("'", "").replace('"', '').lower()

            if clean_response in ["sí", "si"]: 
                return "Sí"
            if clean_response == "no": 
                # NUEVO: Incrementar contador solo en modo fácil
                if self.difficulty == "easy":
                    self.no_counter += 1
                return "No"
            if clean_response == "no relevante": 
                return "No relevante"
            
            self.console.print(f"[bold yellow]Respuesta inválida del Maestro: '{response}'. Reintentando... ({i+1}/{max_retries})[/bold yellow]")
            prompt = f"TAREA: PREGUNTA\n\n---\nTu respuesta anterior '{response}' fue inválida. Debes responder únicamente con 'Sí', 'No', o 'No relevante'.\n---\nHistoria Secreta: \"{self.secret_story}\"\n---\nPregunta del Jugador: \"{question}\""

        self.console.print("[bold red]El Maestro no pudo dar una respuesta válida. Forzando 'No relevante'.[/bold red]")
        return "No relevante"

    def _handle_final_solution(self, solution):
        """Handles the final solution evaluation by the Master."""
        prompt = f"TAREA: EVALUAR\n\n---\nHistoria Secreta: \"{self.secret_story}\"\n---\nSolución propuesta por el Jugador: \"{solution}\""
        final_evaluation = self.master_model.generate_response(
            prompt, 
            system_prompt=self.prompt_master_eval
        )
        
        self.console.print(Panel(f"[bold magenta]Maestro ({self.master_model.model_name}):[/bold magenta]\n{final_evaluation}", title="Evaluación Final", border_style="magenta"))
        self.history["conversation"].append({
            "speaker": "master_final", "text": final_evaluation, "timestamp": datetime.now().isoformat()
        })

    def _parse_player_response(self, response_text):
        """Parses the Player's XML response to extract Thought and Question."""
        thought_match = re.search(r'<PENSAMIENTO>(.*?)</PENSAMIENTO>', response_text, re.DOTALL)
        question_match = re.search(r'<PREGUNTA>(.*?)</PREGUNTA>', response_text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else None
        question = question_match.group(1).strip() if question_match else response_text.strip() # Fallback to full text

        return thought, question
    
    def _is_final_answer(self, text):
        """Detects if a player response is a final answer attempt."""
        text_lower = text.lower()
        
        # Palabras clave que indican respuesta final
        final_keywords = [
            "respuesta:",
            "respuesta final",
            "solución final",
            "solucion final",
            "mi respuesta es",
            "la respuesta es",
            "creo que la respuesta"
        ]
        
        # Buscar keywords
        for keyword in final_keywords:
            if keyword in text_lower:
                return True
        
        # Si la respuesta es muy larga (>300 caracteres), probablemente es explicación de solución
        if len(text) > 300:
            return True
            
        return False

    def _generate_hint(self):
        """Generates a hint based on current game state."""
        # Construir contexto para el Maestro
        conversation_summary = ""
        for entry in self.history["conversation"]:
            if entry["speaker"] == "player":
                conversation_summary += f"Pregunta: {entry['text']}\n"
            elif entry["speaker"] == "master":
                conversation_summary += f"Respuesta: {entry['text']}\n"
        
        prompt = f"""TAREA: GENERAR PISTA

---
Historia Secreta: "{self.secret_story}"
---
Historial de Conversación:
{conversation_summary}
---

Genera UNA pista sutil para ayudar al jugador."""

        try:
            # Cargar prompt de pistas
            with open("prompts/maestro_pista.txt", "r", encoding="utf-8") as f:
                hint_prompt = f.read()
            
            hint_text = self.master_model.generate_response(
                prompt,
                system_prompt=hint_prompt
            ).strip()
            
            self.master_model.clear_history()  # Limpiar para no contaminar
            return hint_text
        except Exception as e:
            self.console.print(f"[bold red]Error al generar pista: {e}[/bold red]")
            return None

    def _display_hint(self, hint_text):
        """Displays a hint to the observer with distinctive formatting."""
        self.console.print("\n" + "=" * 60)
        self.console.print(Panel(
            f"[bold yellow]{hint_text}[/bold yellow]",
            title="[*] PISTA OTORGADA AL JUGADOR",
            border_style="yellow",
            expand=False
        ))
        self.console.print("=" * 60 + "\n")

    def start_game(self):
        """Starts and manages the main game loop."""
        try:
            initial_riddle = self._initialize_story()
            if not initial_riddle:
                return

            self.console.print(Panel(f"[bold magenta]Maestro ({self.master_model.model_name}):[/bold magenta]\n{initial_riddle}", title="Acertijo Inicial", border_style="magenta"))
            
            turn = 1
            max_turns = 15  # NUEVO: Límite máximo de turnos
            conversation_history_for_player = f"Acertijo Inicial: {initial_riddle}\n\n"
            pending_hint = None  # NUEVO: Almacena pista a inyectar en próximo turno

            while True:
                # NUEVO: Verificar límite de turnos
                if turn > max_turns:
                    self.console.print(f"\n[bold red]LÍMITE DE TURNOS ALCANZADO ({max_turns}). Forzando evaluación final...[/bold red]\n")
                    # Forzar evaluación con lo que tenga hasta ahora
                    forced_answer = f"RESPUESTA: Basándome en la información reunida, mi solución es la siguiente: {conversation_history_for_player[-500:]}"
                    self._handle_final_solution(forced_answer)
                    break
                
                # NUEVO: Inyectar pista si hay una pendiente
                if pending_hint:
                    conversation_history_for_player += f"\n[*] INFORMACION ADICIONAL DESCUBIERTA:\n{pending_hint}\n\nTeniendo en cuenta esta nueva informacion, continua tu investigacion.\n\n"
                    pending_hint = None  # Resetear
                
                # NUEVO: Modificar prompt del jugador según el turno
                if turn >= 13:
                    urgency_instruction = f"\n\n[CRÍTICO] Estás en el turno {turn} de {max_turns}. DEBES intentar dar tu RESPUESTA FINAL ahora. Usa el formato: RESPUESTA: [tu explicación completa de lo que ocurrió]."
                else:
                    urgency_instruction = ""
                
                player_prompt = f"Este es el historial de la conversación hasta ahora:\n\n{conversation_history_for_player}\n\nBasado en todo el historial, genera tu siguiente pregunta o la solución final.{urgency_instruction}"
                raw_player_response = self.player_model.generate_response(player_prompt)
                
                # Parse the response
                thought, player_question = self._parse_player_response(raw_player_response)

                # Display Thought (if present)
                if thought:
                    self.console.print(Panel(f"[italic grey50]{thought}[/italic grey50]", title=f"Pensamiento Jugador", border_style="grey50"))

                # Display Question
                self.console.print(Panel(f"[bold cyan]Jugador ({self.player_model.model_name}):[/bold cyan]\n{player_question}", title=f"Turno {turn} - Pregunta", border_style="cyan"))
                
                # Log full response in history (optional: could log parsed parts separately)
                self.history["conversation"].append({
                    "speaker": "player", 
                    "text": player_question, 
                    "thought": thought,
                    "raw_response": raw_player_response,
                    "timestamp": datetime.now().isoformat()
                })

                # MODIFICADO: Usar detección flexible de respuesta final
                if self._is_final_answer(player_question):
                    self.console.print("\n[bold green]Respuesta final detectada. Evaluando...[/bold green]\n")
                    self._handle_final_solution(player_question)
                    break

                master_answer = self._get_master_response(player_question)
                self.console.print(Panel(f"[bold magenta]Maestro ({self.master_model.model_name}):[/bold magenta]\n{master_answer}", title=f"Turno {turn} - Respuesta", border_style="magenta"))
                self.history["conversation"].append({
                    "speaker": "master", "text": master_answer, "timestamp": datetime.now().isoformat()
                })
                
                # NUEVO: Verificar si se debe generar pista automática
                if self.difficulty == "easy" and self.no_counter >= 2 and pending_hint is None:
                    self.console.print("[bold yellow]Se han acumulado 2 respuestas 'No'. Generando pista automática...[/bold yellow]")
                    hint_text = self._generate_hint()
                    if hint_text:
                        self._display_hint(hint_text)
                        pending_hint = hint_text
                    self.no_counter = 0  # Resetear contador
                
                conversation_history_for_player += f"Mi pregunta fue: '{player_question}'\n"
                conversation_history_for_player += f"La respuesta del Maestro fue: '{master_answer}'\n\n"
                turn += 1

                # MODIFICADO: Mostrar advertencia de turnos restantes
                turns_remaining = max_turns - turn + 1
                if turn >= 13:
                    turn_warning = f" [QUEDAN {turns_remaining} TURNOS]"
                else:
                    turn_warning = ""

                # NUEVO: Modificar input para aceptar comando de pista
                if self.difficulty in ["easy", "medium"]:
                    user_input = input(f"\n[Presiona Enter para continuar o escribe 'Pista' para otorgar una pista al jugador{turn_warning}]: ").strip().lower()
                else:  # hard mode
                    user_input = input(f"\n[Presiona Intro para el siguiente turno...{turn_warning}]").strip().lower()
                
                # NUEVO: Procesar comando de pista
                if self.difficulty in ["easy", "medium"] and user_input in ["pista", "hint"]:
                    # Evitar duplicar si ya hay pista automática pendiente
                    if pending_hint is None:
                        self.console.print("[bold yellow]Generando pista manual...[/bold yellow]")
                        hint_text = self._generate_hint()
                        if hint_text:
                            self._display_hint(hint_text)
                            pending_hint = hint_text
                        # Resetear contador automático si está activo
                        if self.difficulty == "easy":
                            self.no_counter = 0
                    else:
                        self.console.print("[bold yellow]Ya hay una pista pendiente de inyectar en el próximo turno.[/bold yellow]")
                # En modo hard, ignorar silenciosamente (no hacer nada si escribe "pista")
                
                self.console.print("---" * 20)

        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Juego interrumpido por el usuario. Guardando progreso...[/bold yellow]")
        finally:
            saver.save_game(self.history, self.save_format)
            self.console.print("[bold green]Juego terminado y guardado.[/bold green]")
