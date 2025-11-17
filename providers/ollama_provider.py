import ollama
from .base_provider import BaseProvider

class OllamaProvider(BaseProvider):
    """Provider for Ollama models."""

    def generate_response(self, prompt, **kwargs):
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            return response["message"]["content"]
        except Exception as e:
            # Handle potential API errors, e.g., model not found, connection error
            print(f"[Error with Ollama provider: {e}]")
            return "Error: Could not get a response from Ollama."
