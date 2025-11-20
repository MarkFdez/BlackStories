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

def load_all_prompts():
    """Carga todos los prompts necesarios desde la carpeta 'prompts/'."""
    prompt_paths = {
        "master_gen": "prompts/maestro_fase1_gen.txt",
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
@click.option('-p1', '--provider1', required=True, type=click.Choice(PROVIDER_MAP.keys()), help='Proveedor del Maestro.')
@click.option('-m1', '--model1', required=True, help='Modelo del Maestro.')
@click.option('-p2', '--provider2', required=True, type=click.Choice(PROVIDER_MAP.keys()), help='Proveedor del Jugador.')
@click.option('-m2', '--model2', required=True, help='Modelo del Jugador.')
@click.option('--save-format', default='md', type=click.Choice(['json', 'txt', 'md']), help='Formato para guardar el historial.')
def main(provider1, model1, provider2, model2, save_format):
    """
    Inicia una partida de Black Stories AI.
    """
    # Cargar todos los prompts por convención
    prompts = load_all_prompts()

    # Crear instancias de los proveedores
    # El prompt inicial del maestro es irrelevante ya que se inyectará dinámicamente
    maestro_model = create_provider(provider1, model1, "") 
    jugador_model = create_provider(provider2, model2, prompts["player"])

    # Iniciar el juego
    game = GameManager(
        master_model=maestro_model,
        player_model=jugador_model,
        save_format=save_format,
        prompt_master_gen=prompts["master_gen"],
        prompt_master_judge=prompts["master_judge"],
        prompt_master_eval=prompts["master_eval"]
    )
    game.start_game()

if __name__ == "__main__":
    main()
