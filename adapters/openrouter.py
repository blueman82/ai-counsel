"""OpenAI-compatible HTTP adapters (OpenRouter, Nebius, etc.)."""
import logging
from typing import Optional, Tuple

from adapters.base_http import BaseHTTPAdapter

logger = logging.getLogger(__name__)


class OpenAIChatCompletionsAdapter(BaseHTTPAdapter):
    """
    Base adapter for OpenAI-compatible chat completions APIs.

    Many LLM providers (OpenRouter, Nebius, Together, etc.) expose
    OpenAI-compatible endpoints. This base class provides shared logic
    for building requests and parsing responses in the standard format.

    Subclasses can customize:
    - provider_name: Used in error messages and logging
    - default_max_tokens: Default max_tokens value (None = omit from request)

    API Format:
        POST /chat/completions
        {
          "model": "model-id",
          "messages": [{"role": "user", "content": "..."}],
          "stream": false,
          "max_tokens": 4096  # optional
        }
    """

    # Subclasses should override these
    provider_name: str = "OpenAI-compatible"
    default_max_tokens: Optional[int] = None

    def build_request(
        self, model: str, prompt: str
    ) -> Tuple[str, dict[str, str], dict]:
        """
        Build OpenAI-compatible chat completions request.

        Args:
            model: Model identifier
            prompt: The prompt to send

        Returns:
            Tuple of (endpoint, headers, body)
        """
        endpoint = "/chat/completions"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }

        body: dict = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }

        # Only include max_tokens if configured
        if self.default_max_tokens is not None:
            body["max_tokens"] = self.default_max_tokens

        return (endpoint, headers, body)

    def parse_response(self, response_json: dict) -> str:
        """
        Parse OpenAI-compatible chat completions response.

        Args:
            response_json: Parsed JSON response

        Returns:
            Extracted response text from first choice

        Raises:
            KeyError: If response doesn't contain expected fields
            IndexError: If choices array is empty
        """
        if "choices" not in response_json:
            raise KeyError(
                f"{self.provider_name} response missing 'choices' field. "
                f"Received keys: {list(response_json.keys())}"
            )

        if len(response_json["choices"]) == 0:
            raise IndexError(f"{self.provider_name} response has empty 'choices' array")

        choice = response_json["choices"][0]

        # Log warning if response was truncated due to token limit
        finish_reason = choice.get("finish_reason", "unknown")
        if finish_reason == "length":
            model = response_json.get("model", "unknown")
            logger.warning(
                f"{self.provider_name} response truncated (finish_reason='length') for model {model}. "
                f"Consider increasing max_tokens or using a model with higher limits."
            )

        if "message" not in choice:
            raise KeyError(
                f"{self.provider_name} choice missing 'message' field. "
                f"Received keys: {list(choice.keys())}"
            )

        message = choice["message"]

        if "content" not in message:
            raise KeyError(
                f"{self.provider_name} message missing 'content' field. "
                f"Received keys: {list(message.keys())}"
            )

        return message["content"]


class OpenRouterAdapter(OpenAIChatCompletionsAdapter):
    """
    Adapter for OpenRouter API.

    OpenRouter provides access to multiple LLM providers through a unified
    OpenAI-compatible API with authentication.

    API Reference: https://openrouter.ai/docs
    Default endpoint: https://openrouter.ai/api/v1
    """

    provider_name = "OpenRouter"
    # OpenRouter benefits from explicit max_tokens to prevent truncation
    default_max_tokens = 4096


class NebiusAdapter(OpenAIChatCompletionsAdapter):
    """
    Adapter for Nebius Token Factory API.

    Nebius Token Factory exposes an OpenAI-compatible chat completions
    endpoint for various open-source and proprietary models.

    API Reference: https://docs.tokenfactory.nebius.com
    Default endpoint: https://api.tokenfactory.nebius.com/v1
    """

    provider_name = "Nebius"
    # Nebius: omit max_tokens to use model defaults
    default_max_tokens = None
