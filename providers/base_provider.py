from abc import ABC, abstractmethod

class BaseProvider(ABC):
    """Abstract base class for all AI providers."""

    def __init__(self, model_name, system_prompt):
        self.model_name = model_name
        self.system_prompt = system_prompt

    @abstractmethod
    def generate_response(self, prompt, **kwargs):
        """
        Generates a response from the provider.

        Args:
            prompt (str): The user's prompt.
            **kwargs: Additional provider-specific arguments.

        Returns:
            str: The generated response.
        """
        pass
