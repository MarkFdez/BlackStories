import click
import sys
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

def read_character_file(filepath):
    """Lee el contenido de un archivo de personalidad."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: El archivo de personaje '{filepath}' no fue encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"Error al leer el archivo '{filepath}': {e}")
        sys.exit(1)

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
@click.option('-c1', '--character1', required=True, type=click.Path(exists=True), help='Ruta al prompt de sistema del Maestro.')
@click.option('-p2', '--provider2', required=True, type=click.Choice(PROVIDER_MAP.keys()), help='Proveedor del Jugador.')
@click.option('-m2', '--model2', required=True, help='Modelo del Jugador.')
@click.option('-c2', '--character2', required=True, type=click.Path(exists=True), help='Ruta al prompt de sistema del Jugador.')
@click.option('--save-format', default='md', type=click.Choice(['json', 'txt', 'md']), help='Formato para guardar el historial.')
def main(provider1, model1, character1, provider2, model2, character2, save_format):
    """
    Inicia una partida de Black Stories AI.
    """
    # Leer los prompts de personalidad
    prompt_maestro = read_character_file(character1)
    prompt_jugador = read_character_file(character2)

    # Crear instancias de los proveedores
    maestro_model = create_provider(provider1, model1, prompt_maestro)
    jugador_model = create_provider(provider2, model2, prompt_jugador)

    # Iniciar el juego
    game = GameManager(maestro_model, jugador_model, save_format)
    game.start_game()

if __name__ == "__main__":
    main()
