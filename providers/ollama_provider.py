import ollama
from .base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    """Provider for Ollama models."""

    def __init__(self, model_name, system_prompt):
        super().__init__(model_name, system_prompt)
        # History is no longer stored in the provider instance
        # self.messages = [{"role": "system", "content": self.system_prompt}]

    def generate_response(self, prompt, system_prompt=None, **kwargs):
        """Generates a stateless response from Ollama."""
        # Use the dynamic system prompt if provided, otherwise use the default one from initialization.
        current_system_prompt = system_prompt if system_prompt else self.system_prompt
        
        messages = [
            {"role": "system", "content": current_system_prompt},
            {"role": "user", "content": prompt},
        ]
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
            )
            return response["message"]["content"]
        except Exception as e:
            raise RuntimeError(f"Ollama connection error: {e}")

    def clear_history(self):
        """No history is stored, so this does nothing."""
        pass
