import anthropic
from .base_provider import BaseProvider
from config import ANTHROPIC_API_KEY

class AnthropicProvider(BaseProvider):
    """Provider for Anthropic models."""

    def __init__(self, model_name, system_prompt):
        super().__init__(model_name, system_prompt)
        if not ANTHROPIC_API_KEY:
            raise ValueError("ANTHROPIC_API_KEY is not set in the environment variables.")
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def generate_response(self, prompt, system_prompt=None, **kwargs):
        current_system_prompt = system_prompt if system_prompt else self.system_prompt
        
        try:
            response = self.client.messages.create(
                model=self.model_name,
                system=current_system_prompt,
                messages=[
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1024, # Example: adjust as needed
            )
            return response.content[0].text
        except Exception as e:
            print(f"[Error with Anthropic provider: {e}]")
            return "Error: Could not get a response from Anthropic."

    def clear_history(self):
        """Anthropic provider is stateless in this implementation."""
        pass
