
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
                # The first call to the master should have a simple prompt
                initial_prompt = "Genera una nueva Black Story."
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
        """Gets a validated 'Sí/No/No relevante' response from the Master."""
        prompt = f"""
        Historia Secreta: "{self.secret_story}"
        ---
        Pregunta del Jugador: "{question}"
        ---
        Basado en la historia secreta, responde ESTRICTAMENTE con "Sí", "No", o "No relevante".
        """
        
        max_retries = 3
        for _ in range(max_retries):
            response = self.master_model.generate_response(prompt).strip().lower()
            # Clean up potential markdown or quotes
            response = response.replace("*", "").replace("'", "").replace('"', '')
            
            if response in ["sí", "si"]: return "Sí"
            if response == "no": return "No"
            if response == "no relevante": return "No relevante"
        
        self.console.print("[bold yellow]El Maestro dio una respuesta inválida. Se forzará 'No relevante'.[/bold yellow]")
        return "No relevante"

    def _handle_final_solution(self, solution):
        """Handles the final solution evaluation by the Master."""
        prompt = f"""
        Historia Secreta: "{self.secret_story}"
        ---
        Solución propuesta por el Jugador: "{solution}"
        ---
        Evalúa si la solución es correcta. Anuncia si ha acertado o fallado y revela la historia secreta completa.
        """
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
            
            last_response = initial_riddle
            turn = 1

            while True:
                # Player's turn
                player_prompt = f"Contexto: {last_response}\n\nBasado en el contexto, genera tu siguiente pregunta o la solución final."
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
                
                last_response = f"Mi última pregunta fue '{player_question}' y la respuesta fue '{master_answer}'."
                turn += 1

                # Pause for user
                input("\n[Presiona Intro para el siguiente turno...]")
                self.console.print("---" * 20)

        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Juego interrumpido por el usuario. Guardando progreso...[/bold yellow]")
        finally:
            saver.save_game(self.history, self.save_format)
            self.console.print("[bold green]Juego terminado y guardado.[/bold green]")
