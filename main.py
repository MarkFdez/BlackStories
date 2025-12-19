import click
import sys
import os
from game_manager import GameManager
from providers.ollama_provider import OllamaProvider
from providers.gemini_provider import GeminiProvider
from providers.openai_provider import OpenAIProvider
from providers.anthropic_provider import AnthropicProvider
from providers.grok_provider import GrokProvider

# Mapeo de proveedores a sus clases
PROVIDER_MAP = {
    "ollama": OllamaProvider,
    "gemini": GeminiProvider,
    "openai": OpenAIProvider,
    "anthropic": AnthropicProvider,
    "grok": GrokProvider,
}

def load_prompt(file_path):
    """Lee el contenido de un archivo de prompt específico."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: El archivo de prompt requerido '{file_path}' no fue encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"Error al leer el archivo '{file_path}': {e}")
        sys.exit(1)

def interactive_mode():
    """Modo interactivo para configurar el juego sin parámetros CLI."""
    from rich.console import Console
    
    console = Console()
    
    # Mostrar mensaje de bienvenida
    console.print("\n" + "=" * 60, style="cyan")
    console.print("BLACK STORIES AI - Juego de Misterio".center(60), style="bold cyan")
    console.print("=" * 60 + "\n", style="cyan")
    
    console.print("Bienvenido al juego de Black Stories con IA.")
    console.print("Dos modelos de IA competirán: un Maestro crea el misterio,")
    console.print("un Jugador intenta resolverlo.\n")
    
    console.print("=" * 60 + "\n", style="cyan")
    
    console.print("[bold]PROVEEDORES DISPONIBLES:[/bold]")
    console.print("  1. [green]Gemini[/green] (Google)")
    console.print("  2. [blue]Ollama[/blue] (Local)\n")
    
    console.print("[bold]MODELOS SUGERIDOS:[/bold]")
    console.print("  [green]Gemini:[/green]  gemini-2.0-flash-exp, gemini-1.5-flash, gemini-1.5-pro")
    console.print("  [blue]Ollama:[/blue]  llama3.2:3b, llama3:8b, qwen2.5:7b\n")
    
    console.print("[bold]NIVELES DE DIFICULTAD:[/bold]")
    console.print("  [yellow]facil[/yellow]   - Misterios simples (3-4 pasos), pistas automaticas cada 2 'No'")
    console.print("  [yellow]medio[/yellow]   - Complejidad normal, pistas solo manuales")
    console.print("  [yellow]dificil[/yellow] - Mas complejo (4-5 pasos), sin pistas\n")
    
    console.print("=" * 60 + "\n", style="cyan")
    
    console.print("[bold]FORMATO DE INICIO:[/bold]")
    console.print("Escribe: [cyan]<proveedor1> <modelo1> <proveedor2> <modelo2> <dificultad>[/cyan]\n")
    
    console.print("[bold]EJEMPLO:[/bold]")
    console.print("[green]gemini gemini-1.5-flash gemini gemini-1.5-flash medio[/green]\n")
    
    console.print("=" * 60 + "\n", style="cyan")
    
    # Obtener input del usuario
    while True:
        user_input = input("Tu turno (o 'q' para salir): ").strip()
        
        if user_input.lower() == 'q':
            console.print("\n[yellow]Saliendo...[/yellow]")
            sys.exit(0)
        
        # Parsear input
        parts = user_input.split()
        
        if len(parts) < 4:
            console.print("[red]Error: Formato incompleto. Necesitas al menos 4 elementos (proveedor1 modelo1 proveedor2 modelo2)[/red]")
            console.print("[yellow]Ejemplo: gemini gemini-1.5-flash gemini gemini-1.5-flash medio[/yellow]\n")
            continue
        
        provider1 = parts[0].lower()
        model1 = parts[1]
        provider2 = parts[2].lower()
        model2 = parts[3]
        difficulty = parts[4].lower() if len(parts) > 4 else 'medio'
        
        # Validar proveedores
        if provider1 not in ['gemini', 'ollama'] or provider2 not in ['gemini', 'ollama']:
            console.print(f"[red]Error: Solo se permiten proveedores 'gemini' u 'ollama'[/red]\n")
            continue
        
        # Todo validado, retornar
        return provider1, model1, provider2, model2, difficulty

def load_all_prompts(difficulty="medium"):
    """Carga todos los prompts necesarios desde la carpeta 'prompts/' según dificultad."""
    # Mapear dificultad a sufijo de archivo
    difficulty_suffix = {
        'easy': 'facil',
        'medium': 'medio',
        'hard': 'dificil'
    }
    suffix = difficulty_suffix.get(difficulty, 'medio')
    
    prompt_paths = {
        "master_gen": f"prompts/maestro_fase1_gen_{suffix}.txt",
        "master_judge": "prompts/maestro_fase2_juez.txt",
        "master_eval": "prompts/maestro_fase3_eval.txt",
        "player": "prompts/jugador.txt",
    }
    
    prompts = {key: load_prompt(path) for key, path in prompt_paths.items()}
    return prompts

def create_provider(provider_name, model_name, character_prompt):
    """Crea una instancia del proveedor de IA solicitado."""
    provider_class = PROVIDER_MAP.get(provider_name)
    if not provider_class:
        print(f"Error: Proveedor '{provider_name}' no es válido. Opciones: {list(PROVIDER_MAP.keys())}")
        sys.exit(1)
    try:
        return provider_class(model_name, character_prompt)
    except ValueError as e:
        print(f"Error de configuración para {provider_name}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error al inicializar el proveedor {provider_name}: {e}")
        sys.exit(1)

@click.command()
@click.option('-p1', '--provider1', required=False, type=click.Choice(PROVIDER_MAP.keys()), help='Proveedor del Maestro.')
@click.option('-m1', '--model1', required=False, help='Modelo del Maestro.')
@click.option('-p2', '--provider2', required=False, type=click.Choice(PROVIDER_MAP.keys()), help='Proveedor del Jugador.')
@click.option('-m2', '--model2', required=False, help='Modelo del Jugador.')
@click.option('--difficulty', default='medium', type=click.Choice(['easy', 'medium', 'hard', 'fácil', 'facil', 'medio', 'difícil', 'dificil'], case_sensitive=False), help='Nivel de dificultad del juego.')
@click.option('--save-format', default='md', type=click.Choice(['json', 'txt', 'md']), help='Formato para guardar el historial.')
def main(provider1, model1, provider2, model2, difficulty, save_format):
    """
    Inicia una partida de Black Stories AI.
    """
    # Si no hay argumentos, entrar en modo interactivo
    if not provider1 or not model1 or not provider2 or not model2:
        provider1, model1, provider2, model2, difficulty = interactive_mode()
    
    # Validar que sean gemini u ollama
    allowed_providers = ['gemini', 'ollama']
    if provider1 not in allowed_providers or provider2 not in allowed_providers:
        print(f"Error: Solo se permiten proveedores: {allowed_providers}")
        sys.exit(1)
    
    # Normalizar dificultad a valores estándar
    difficulty_map = {
        'easy': 'easy', 'fácil': 'easy', 'facil': 'easy',
        'medium': 'medium', 'medio': 'medium',
        'hard': 'hard', 'difícil': 'hard', 'dificil': 'hard'
    }
    normalized_difficulty = difficulty_map.get(difficulty.lower(), 'medium')
    
    # Cargar todos los prompts según dificultad
    prompts = load_all_prompts(normalized_difficulty)

    # Crear instancias de los proveedores
    # El prompt inicial del maestro es irrelevante ya que se inyectará dinámicamente
    maestro_model = create_provider(provider1, model1, "") 
    jugador_model = create_provider(provider2, model2, prompts["player"])

    # Iniciar el juego
    game = GameManager(
        master_model=maestro_model,
        player_model=jugador_model,
        save_format=save_format,
        difficulty=normalized_difficulty,
        prompt_master_gen=prompts["master_gen"],
        prompt_master_judge=prompts["master_judge"],
        prompt_master_eval=prompts["master_eval"]
    )
    game.start_game()

if __name__ == "__main__":
    main()
