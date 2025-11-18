
import json
import time
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
import saver

class GameManager:
    def __init__(self, master_model, player_model, save_format="md"):
        self.master_model = master_model
        self.player_model = player_model
        self.save_format = save_format
        self.console = Console()
        self.secret_story = ""
        self.history = {
            "metadata": {
                "master_provider": master_model.__class__.__name__,
                "master_model": master_model.model_name,
                "player_provider": player_model.__class__.__name__,
                "player_model": player_model.model_name,
                "master_prompt": master_model.system_prompt,
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
                # Use the state machine prompt
                initial_prompt = "TAREA: GENERAR"
                response_text = self.master_model.generate_response(initial_prompt)
                
                # Clean the response to get only the JSON part
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start == -1 or json_end == 0:
                    raise json.JSONDecodeError("No JSON object found in the response.", response_text, 0)
                
                json_str = response_text[json_start:json_end]
                story_data = json.loads(json_str)

                if "historia_secreta" in story_data and "acertijo_inicial" in story_data:
                    self.secret_story = story_data["historia_secreta"]
                    self.history["story"] = story_data
                    return story_data["acertijo_inicial"]
                else:
                    raise ValueError("El JSON recibido no tiene las claves 'historia_secreta' o 'acertijo_inicial'.")

            except (json.JSONDecodeError, ValueError) as e:
                self.console.print(f"[bold red]Error al parsear el misterio del Maestro (intento {attempt + 1}/{max_retries}): {e}[/bold red]")
                if attempt == max_retries - 1:
                    self.console.print("[bold red]No se pudo iniciar el juego. El Maestro no proporcionó un JSON válido.[/bold red]")
                    return None
                time.sleep(1) # Wait before retrying
        return None

    def _get_master_response(self, question):
        """Gets a validated 'Sí/No/No relevante' response from the Master with self-correction."""
        prompt = f"TAREA: PREGUNTA\n\n---\nHistoria Secreta: \"{self.secret_story}\"\n---\nPregunta del Jugador: \"{question}\""
        
        max_retries = 3
        for i in range(max_retries):
            response = self.master_model.generate_response(prompt).strip()
            clean_response = response.replace("*", "").replace("'", "").replace('"', '').lower()

            if clean_response in ["sí", "si"]:
                return "Sí"
            if clean_response == "no":
                return "No"
            if clean_response == "no relevante":
                return "No relevante"
            
            # If the response is invalid, try to correct it
            self.console.print(f"[bold yellow]Respuesta inválida del Maestro: '{response}'. Reintentando... ({i+1}/{max_retries})[/bold yellow]")
            prompt = f"TAREA: PREGUNTA\n\n---\nTu respuesta anterior '{response}' fue inválida. Debes responder únicamente con 'Sí', 'No', o 'No relevante'.\n---\nHistoria Secreta: \"{self.secret_story}\"\n---\nPregunta del Jugador: \"{question}\""

        self.console.print("[bold red]El Maestro no pudo dar una respuesta válida. Forzando 'No relevante'.[/bold red]")
        return "No relevante"

    def _handle_final_solution(self, solution):
        """Handles the final solution evaluation by the Master."""
        prompt = f"TAREA: EVALUAR\n\n---\nHistoria Secreta: \"{self.secret_story}\"\n---\nSolución propuesta por el Jugador: \"{solution}\""
        final_evaluation = self.master_model.generate_response(prompt)
        
        self.console.print(Panel(f"[bold magenta]Maestro ({self.master_model.model_name}):[/bold magenta]\n{final_evaluation}", title="Evaluación Final", border_style="magenta"))
        self.history["conversation"].append({
            "speaker": "master_final",
            "text": final_evaluation,
            "timestamp": datetime.now().isoformat()
        })

    def start_game(self):
        """Starts and manages the main game loop."""
        try:
            initial_riddle = self._initialize_story()
            if not initial_riddle:
                return

            self.console.print(Panel(f"[bold magenta]Maestro ({self.master_model.model_name}):[/bold magenta]\n{initial_riddle}", title="Acertijo Inicial", border_style="magenta"))
            
            turn = 1
            conversation_history_for_player = f"Acertijo Inicial: {initial_riddle}\n\n"

            while True:
                # Player's turn
                player_prompt = f"Este es el historial de la conversación hasta ahora:\n\n{conversation_history_for_player}\n\nBasado en todo el historial, genera tu siguiente pregunta o la solución final."
                player_question = self.player_model.generate_response(player_prompt)
                
                self.console.print(Panel(f"[bold cyan]Jugador ({self.player_model.model_name}):[/bold cyan]\n{player_question}", title=f"Turno {turn} - Pregunta", border_style="cyan"))
                self.history["conversation"].append({
                    "speaker": "player",
                    "text": player_question,
                    "timestamp": datetime.now().isoformat()
                })

                if player_question.lower().startswith("respuesta:"):
                    self._handle_final_solution(player_question)
                    break

                # Master's turn
                master_answer = self._get_master_response(player_question)
                self.console.print(Panel(f"[bold magenta]Maestro ({self.master_model.model_name}):[/bold magenta]\n{master_answer}", title=f"Turno {turn} - Respuesta", border_style="magenta"))
                self.history["conversation"].append({
                    "speaker": "master",
                    "text": master_answer,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Update conversation history for the player
                conversation_history_for_player += f"Mi pregunta fue: '{player_question}'\n"
                conversation_history_for_player += f"La respuesta del Maestro fue: '{master_answer}'\n\n"
                turn += 1

                # Pause for user
                input("\n[Presiona Intro para el siguiente turno...]")
                self.console.print("---" * 20)

        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Juego interrumpido por el usuario. Guardando progreso...[/bold yellow]")
        finally:
            saver.save_game(self.history, self.save_format)
            self.console.print("[bold green]Juego terminado y guardado.[/bold green]")
