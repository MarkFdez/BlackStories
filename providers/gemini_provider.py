import google.generativeai as genai
from .base_provider import BaseProvider
from config import GEMINI_API_KEY

class GeminiProvider(BaseProvider):
    """Provider for Google Gemini models."""

    def __init__(self, model_name, system_prompt):
        super().__init__(model_name, system_prompt)
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
        genai.configure(api_key=GEMINI_API_KEY)
        # Don't create client with empty system_instruction (Gemini rejects it)
        if self.system_prompt:
            self.client = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt
            )
        else:
            self.client = genai.GenerativeModel(model_name=self.model_name)

    def generate_response(self, prompt, system_prompt=None, **kwargs):
        # Use the dynamic system prompt if provided
        current_system_prompt = system_prompt if system_prompt else self.system_prompt
        
        # Re-create the client with the specific system instruction for this call
        client = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=current_system_prompt
        )

        try:
            response = client.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[Error with Gemini provider: {e}]")
            return "Error: Could not get a response from Gemini."

    def clear_history(self):
        """Gemini provider is stateless in this implementation."""
        pass
