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
        self.client = genai.GenerativeModel(
            model_name=self.model_name,
            system_instruction=self.system_prompt
        )

    def generate_response(self, prompt, **kwargs):
        try:
            response = self.client.generate_content(prompt)
            return response.text
        except Exception as e:
            print(f"[Error with Gemini provider: {e}]")
            return "Error: Could not get a response from Gemini."
