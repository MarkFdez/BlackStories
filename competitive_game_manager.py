import json
import time
import re
import random
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import saver


class CompetitiveGameManager:
    """Gestor de partidas competitivas 1v1 - Clase independiente sin herencia."""
    
    def __init__(self, master_model, player1_model, player2_model, save_format="md", 
                 difficulty="medium", prompt_master_gen="", prompt_master_judge="", 
                 prompt_master_eval_competitive=""):
        self.master_model = master_model
        self.player_models = [player1_model, player2_model]
        self.current_player_index = random.choice([0, 1])  # Inicio aleatorio
        self.save_format = save_format
        self.difficulty = difficulty
        self.console = Console()
        self.secret_story = ""
        
        # Prompts
        self.prompt_master_gen = prompt_master_gen
        self.prompt_master_judge = prompt_master_judge
        self.prompt_master_eval_competitive = prompt_master_eval_competitive
        
        # Historia adaptada para modo competitivo
        self.history = {
            "metadata": {
                "mode": "competitive_1v1",
                "difficulty": difficulty,
                "master_provider": master_model.__class__.__name__,
                "master_model": master_model.model_name,
                "player1_provider": player1_model.__class__.__name__,
                "player1_model": player1_model.model_name,
                "player2_provider": player2_model.__class__.__name__,
                "player2_model": player2_model.model_name,
                "starting_player": self.current_player_index + 1,
                "master_prompt_gen": self.prompt_master_gen,
                "master_prompt_judge": self.prompt_master_judge,
                "master_prompt_eval": self.prompt_master_eval_competitive,
                "game_date": datetime.now().isoformat(),
            },
            "story": {},
            "conversation": [],
            "evaluation": {}
        }
    
    def _switch_player(self):
        """Alterna entre jugadores."""
        self.current_player_index = 1 - self.current_player_index
    
    def _get_current_player(self):
        """Retorna el modelo del jugador actual."""
        return self.player_models[self.current_player_index]
    
    def _get_other_player(self):
        """Retorna el modelo del otro jugador."""
        return self.player_models[1 - self.current_player_index]
    
    def _initialize_story(self):
        """Llama al Maestro para generar el misterio inicial en formato JSON."""
        self.console.print(Panel(
            "[bold yellow]El Maestro está creando un nuevo misterio...[/bold yellow]",
            border_style="yellow"
        ))
        
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
        """Obtiene una respuesta validada 'Sí/No/No relevante' del Maestro con auto-corrección."""
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
                return "No"
            if clean_response == "no relevante": 
                return "No relevante"
            
            self.console.print(f"[bold yellow]Respuesta inválida del Maestro: '{response}'. Reintentando... ({i+1}/{max_retries})[/bold yellow]")
            prompt = f"TAREA: PREGUNTA\n\n---\nTu respuesta anterior '{response}' fue inválida. Debes responder únicamente con 'Sí', 'No', o 'No relevante'.\n---\nHistoria Secreta: \"{self.secret_story}\"\n---\nPregunta del Jugador: \"{question}\""

        self.console.print("[bold red]El Maestro no pudo dar una respuesta válida. Forzando 'No relevante'.[/bold red]")
        return "No relevante"
    
    def _parse_player_response(self, response_text):
        """Parsea la respuesta XML del jugador para extraer Pensamiento y Pregunta."""
        thought_match = re.search(r'<PENSAMIENTO>(.*?)</PENSAMIENTO>', response_text, re.DOTALL)
        question_match = re.search(r'<PREGUNTA>(.*?)</PREGUNTA>', response_text, re.DOTALL)

        thought = thought_match.group(1).strip() if thought_match else None
        question = question_match.group(1).strip() if question_match else response_text.strip()

        return thought, question
    
    def _is_final_answer(self, text):
        """Detecta si una respuesta es un intento de solución final."""
        text_lower = text.lower()
        
        final_keywords = [
            "respuesta:",
            "respuesta final",
            "solución final",
            "solucion final",
            "mi respuesta es",
            "la respuesta es",
            "creo que la respuesta"
        ]
        
        for keyword in final_keywords:
            if keyword in text_lower:
                return True
        
        if len(text) > 300:
            return True
            
        return False
    
    def _build_shared_context(self, initial_riddle):
        """Construye el contexto compartido visible para ambos jugadores."""
        context = f"Acertijo Inicial: {initial_riddle}\n\n"
        for entry in self.history["conversation"]:
            if entry["speaker"].startswith("player"):
                player_num = entry["speaker"][-1]
                context += f"[Jugador {player_num}] {entry['text']}\n"
            elif entry["speaker"] == "master":
                context += f"[Maestro] {entry['text']}\n\n"
        return context
    
    def _force_solution_from_player(self, player_index, shared_context):
        """Fuerza a un jugador a dar su solución final."""
        player = self.player_models[player_index]
        forced_prompt = f"""
{shared_context}

[ATENCIÓN CRÍTICA] Tu oponente ha presentado su solución final.
Es OBLIGATORIO que presentes tu propia solución AHORA.
Basándote SOLO en el historial anterior, proporciona tu respuesta final.
Formato: RESPUESTA: [tu explicación completa del misterio]
"""
        return player.generate_response(forced_prompt)
    
    def _parse_competitive_evaluation(self, response_text):
        """Parsea la evaluación JSON del Maestro."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                json_start = response_text.find('{')
                json_end = response_text.rfind('}') + 1
                if json_start == -1 or json_end == 0:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
                
                json_str = response_text[json_start:json_end]
                evaluation = json.loads(json_str)
                
                # Validar campos requeridos
                required = ["jugador1", "jugador2", "ganador"]
                if all(k in evaluation for k in required):
                    return evaluation
                else:
                    raise ValueError(f"JSON inválido: faltan campos {required}")
            
            except (json.JSONDecodeError, ValueError) as e:
                self.console.print(f"[yellow]Error parseando evaluación (intento {attempt+1}/{max_retries}): {e}[/yellow]")
                if attempt == max_retries - 1:
                    # Fallback a empate
                    return {
                        "jugador1": {"evaluacion": "Error en evaluación", "precision": 50},
                        "jugador2": {"evaluacion": "Error en evaluación", "precision": 50},
                        "ganador": "empate",
                        "historia_secreta": self.secret_story
                    }
                time.sleep(1)
        
    def _handle_competitive_evaluation(self, solution1, solution2):
        """Envía ambas soluciones al Maestro para evaluación."""
        prompt = f"""
TAREA: EVALUAR COMPETITIVO

---
Historia Secreta: "{self.secret_story}"
---
Solución Jugador 1: "{solution1}"
---
Solución Jugador 2: "{solution2}"
---
"""
        self.console.print("\n[bold cyan]⏳ El Maestro está evaluando ambas soluciones...[/bold cyan]\n")
        
        response = self.master_model.generate_response(
            prompt, 
            system_prompt=self.prompt_master_eval_competitive
        )
        
        evaluation = self._parse_competitive_evaluation(response)
        
        # Mostrar resultados
        self._display_competitive_results(evaluation)
        
        # Guardar en historial
        self.history["evaluation"] = evaluation
    
    def _display_competitive_results(self, evaluation):
        """Muestra los resultados de forma visual con Rich."""
        # Tabla comparativa
        table = Table(title="🏆 EVALUACIÓN FINAL", show_header=True, header_style="bold")
        table.add_column("Jugador", style="cyan", width=30)
        table.add_column("Precisión", justify="right", width=12)
        table.add_column("Evaluación", style="dim", width=60)
        
        j1 = evaluation["jugador1"]
        j2 = evaluation["jugador2"]
        
        table.add_row(
            f"Jugador 1\n({self.player_models[0].model_name})",
            f"{j1.get('precision', 'N/A')}%",
            j1.get('evaluacion', 'N/A')[:100] + "..." if len(j1.get('evaluacion', '')) > 100 else j1.get('evaluacion', 'N/A')
        )
        table.add_row(
            f"Jugador 2\n({self.player_models[1].model_name})",
            f"{j2.get('precision', 'N/A')}%",
            j2.get('evaluacion', 'N/A')[:100] + "..." if len(j2.get('evaluacion', '')) > 100 else j2.get('evaluacion', 'N/A')
        )
        
        self.console.print(table)
        
        # Ganador
        winner = evaluation["ganador"]
        if winner == "jugador1":
            self.console.print(Panel(
                f"🥇 [bold green]¡GANADOR: JUGADOR 1![/bold green]\n\n{self.player_models[0].model_name}",
                border_style="green",
                title="Victoria"
            ))
        elif winner == "jugador2":
            self.console.print(Panel(
                f"🥇 [bold green]¡GANADOR: JUGADOR 2![/bold green]\n\n{self.player_models[1].model_name}",
                border_style="green",
                title="Victoria"
            ))
        else:
            self.console.print(Panel(
                f"🤝 [bold yellow]RESULTADO: EMPATE[/bold yellow]\n\nAmbos jugadores demostraron habilidades similares",
                border_style="yellow",
                title="Empate Técnico"
            ))
        
        # Historia secreta
        self.console.print(Panel(
            f"[bold magenta]Historia Secreta:[/bold magenta]\n\n{evaluation.get('historia_secreta', self.secret_story)}",
            title="🔍 La Verdad Revelada",
            border_style="magenta"
        ))
    
    def start_competitive_game(self):
        """Inicia el loop de juego competitivo."""
        try:
            # Inicializar historia
            initial_riddle = self._initialize_story()
            if not initial_riddle:
                return
            
            self.console.print(Panel(
                f"[bold magenta]Maestro:[/bold magenta]\n{initial_riddle}",
                title="🎲 Acertijo Inicial - Modo Competitivo 1v1",
                border_style="magenta"
            ))
            
            # Mostrar quién empieza
            starting_player_num = self.current_player_index + 1
            self.console.print(f"\n[bold cyan]🎲 Jugador {starting_player_num} comienza la partida[/bold cyan]\n")
            
            turn = 1
            MAX_TURNS = 16
            solutions = [None, None]  # Almacenar soluciones de cada jugador
            
            while turn <= MAX_TURNS:
                # Construir contexto compartido
                shared_context = self._build_shared_context(initial_riddle)
                
                # Advertencias de turno crítico
                if turn == 13:
                    self.console.print(f"\n[bold yellow]⚠️  TURNO CRÍTICO: Quedan solo 4 turnos[/bold yellow]\n")
                elif turn == 16:
                    self.console.print(f"\n[bold red]🚨 ÚLTIMO TURNO: Los jugadores DEBEN presentar sus soluciones[/bold red]\n")
                
                current_player = self._get_current_player()
                player_num = self.current_player_index + 1
                
                # Prompt con urgencia si es turno >= 13
                if turn >= 13:
                    urgency = f"\n\n[TURNO {turn}/{MAX_TURNS}] Quedan pocos turnos. Considera presentar tu solución final."
                else:
                    urgency = ""
                
                player_prompt = f"{shared_context}\n\nGenera tu siguiente pregunta o solución final.{urgency}"
                raw_response = current_player.generate_response(player_prompt)
                
                # Parse respuesta
                thought, question = self._parse_player_response(raw_response)
                
                # Display
                border_colors = ["cyan", "green"]
                if thought:
                    self.console.print(Panel(
                        f"[italic grey50]{thought}[/italic grey50]",
                        title=f"💭 Pensamiento Jugador {player_num}",
                        border_style="grey50"
                    ))
                
                self.console.print(Panel(
                    f"[bold {border_colors[self.current_player_index]}]Jugador {player_num} ({current_player.model_name}):[/bold {border_colors[self.current_player_index]}]\n{question}",
                    title=f"Turno {turn} - Jugador {player_num}",
                    border_style=border_colors[self.current_player_index]
                ))
                
                # Guardar en historial
                self.history["conversation"].append({
                    "speaker": f"player{player_num}",
                    "text": question,
                    "thought": thought,
                    "timestamp": datetime.now().isoformat(),
                    "turn": turn
                })
                
                # Detectar solución final
                if self._is_final_answer(question):
                    self.console.print(f"\n[bold yellow]🏁 Jugador {player_num} ha presentado su solución final[/bold yellow]\n")
                    solutions[self.current_player_index] = question
                    
                    # BLIND SHOWDOWN: Forzar al otro jugador
                    other_player_index = 1 - self.current_player_index
                    other_player_num = other_player_index + 1
                    
                    self.console.print(f"[bold cyan]⏳ Forzando solución del Jugador {other_player_num}...[/bold cyan]\n")
                    
                    forced_solution = self._force_solution_from_player(
                        other_player_index,
                        shared_context
                    )
                    solutions[other_player_index] = forced_solution
                    
                    # Mostrar solución forzada
                    self.console.print(Panel(
                        f"[bold {border_colors[other_player_index]}]Jugador {other_player_num} (forzado):[/bold {border_colors[other_player_index]}]\n{forced_solution}",
                        title=f"Solución Forzada - Jugador {other_player_num}",
                        border_style=border_colors[other_player_index]
                    ))
                    
                    self.history["conversation"].append({
                        "speaker": f"player{other_player_num}",
                        "text": forced_solution,
                        "forced": True,
                        "timestamp": datetime.now().isoformat()
                    })
                    
                    # Evaluar ambas soluciones
                    self._handle_competitive_evaluation(solutions[0], solutions[1])
                    break
                
                # Si es turno 16 y nadie dio solución, forzar a ambos
                if turn == MAX_TURNS:
                    self.console.print(f"\n[bold red]⏰ TIEMPO AGOTADO - Forzando soluciones finales[/bold red]\n")
                    
                    for i in range(2):
                        if solutions[i] is None:
                            self.console.print(f"[cyan]Forzando solución del Jugador {i+1}...[/cyan]")
                            solutions[i] = self._force_solution_from_player(i, shared_context)
                            self.history["conversation"].append({
                                "speaker": f"player{i+1}",
                                "text": solutions[i],
                                "forced": True,
                                "timestamp": datetime.now().isoformat()
                            })
                    
                    self._handle_competitive_evaluation(solutions[0], solutions[1])
                    break
                
                # Obtener respuesta del Maestro
                master_answer = self._get_master_response(question)
                self.console.print(Panel(
                    f"[bold magenta]Maestro:[/bold magenta]\n{master_answer}",
                    title=f"Turno {turn} - Respuesta",
                    border_style="magenta"
                ))
                
                self.history["conversation"].append({
                    "speaker": "master",
                    "text": master_answer,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Alternar jugador
                self._switch_player()
                turn += 1
                
                # Pause para observar
                input("\n[Presiona Enter para continuar al siguiente turno...]")
                self.console.print("---" * 20)
        
        except KeyboardInterrupt:
            self.console.print("\n[bold yellow]Juego interrumpido por el usuario[/bold yellow]")
        finally:
            saver.save_game(self.history, self.save_format)
            self.console.print("[bold green]Partida guardada exitosamente[/bold green]")
