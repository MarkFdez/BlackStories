from openai import OpenAI
from .base_provider import BaseProvider
from config import OPENAI_API_KEY

class OpenAIProvider(BaseProvider):
    """Provider for OpenAI models."""

    def __init__(self, model_name, system_prompt):
        super().__init__(model_name, system_prompt)
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY is not set in the environment variables.")
        self.client = OpenAI(api_key=OPENAI_API_KEY)

    def generate_response(self, prompt, **kwargs):
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"[Error with OpenAI provider: {e}]")
            return "Error: Could not get a response from OpenAI."
