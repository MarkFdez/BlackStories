import json
from datetime import datetime

def get_unique_filename(extension):
    """Generates a unique filename based on the current timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"blackstory_{timestamp}.{extension}"

def save_game(history, save_format="md"):
    """Saves the game history to a file in the specified format."""
    filename = get_unique_filename(save_format)
    
    if save_format == "json":
        content = _format_json(history)
    elif save_format == "txt":
        content = _format_txt(history)
    else:  # Default to markdown
        content = _format_md(history)
        
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"\n[Game saved to {filename}]")
    except IOError as e:
        print(f"\n[Error saving game: {e}]")

def _format_md(history):
    """Formats the history as a Markdown string."""
    meta = history.get("metadata", {})
    story = history.get("story", {})
    convo = history.get("conversation", [])

    md = f"# Black Story Game - {meta.get('game_date', '')}\n\n"
    md += "## Configuración\n"
    md += f"- **Maestro:** {meta.get('master_provider')} ({meta.get('master_model')})\n"
    md += f"- **Jugador:** {meta.get('player_provider')} ({meta.get('player_model')})\n\n"
    
    md += "## Prompts\n"
    md += f"### Prompt del Maestro\n```\n{meta.get('master_prompt', '')}\n```\n"
    md += f"### Prompt del Jugador\n```\n{meta.get('player_prompt', '')}\n```\n\n"

    md += "## El Misterio\n"
    md += f"### Acertijo Inicial\n> {story.get('acertijo_inicial', 'N/A')}\n\n"
    md += f"### Historia Secreta\n> {story.get('historia_secreta', 'N/A')}\n\n"

    md += "## Conversación\n"
    for turn in convo:
        speaker = turn.get('speaker', 'unknown')
        text = turn.get('text', '')
        timestamp = turn.get('timestamp', '')
        
        if speaker == "player":
            md += f"**Jugador ({timestamp}):**\n{text}\n\n---\n"
        elif speaker == "master":
            md += f"**Maestro ({timestamp}):**\n> {text}\n\n"
        elif speaker == "master_final":
            md += f"**Evaluación Final del Maestro ({timestamp}):**\n> {text}\n\n"
            
    return md

def _format_json(history):
    """Formats the history as a JSON string."""
    # This will be implemented with the full history structure
    return json.dumps(history, indent=2, ensure_ascii=False)

def _format_txt(history):
    """Formats the history as a plain text string."""
    meta = history.get("metadata", {})
    story = history.get("story", {})
    convo = history.get("conversation", [])

    txt = f"Black Story Game - {meta.get('game_date', '')}\n"
    txt += "=" * 40 + "\n\n"
    
    txt += "CONFIGURACIÓN\n"
    txt += f"  Maestro: {meta.get('master_provider')} ({meta.get('master_model')})\n"
    txt += f"  Jugador: {meta.get('player_provider')} ({meta.get('player_model')})\n\n"

    txt += "PROMPTS\n"
    txt += f"  Prompt del Maestro:\n{meta.get('master_prompt', '')}\n\n"
    txt += f"  Prompt del Jugador:\n{meta.get('player_prompt', '')}\n\n"

    txt += "EL MISTERIO\n"
    txt += f"  Acertijo Inicial: {story.get('acertijo_inicial', 'N/A')}\n"
    txt += f"  Historia Secreta: {story.get('historia_secreta', 'N/A')}\n\n"

    txt += "CONVERSACIÓN\n"
    txt += "-" * 40 + "\n"
    for turn in convo:
        speaker = turn.get('speaker', 'unknown')
        text = turn.get('text', '')
        timestamp = turn.get('timestamp', '')
        
        if speaker == "player":
            txt += f"Jugador ({timestamp}):\n{text}\n\n"
        elif speaker == "master":
            txt += f"Maestro ({timestamp}):\n{text}\n\n"
        elif speaker == "master_final":
            txt += f"Evaluación Final ({timestamp}):\n{text}\n\n"
            
    return txt
