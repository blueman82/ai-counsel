"""OpenAI HTTP adapter with support for Chat Completions and Responses APIs."""
import logging
from typing import List, Optional, Tuple, Union

from adapters.openrouter import OpenAIChatCompletionsAdapter

logger = logging.getLogger(__name__)

# Default prefixes for models that use the Responses API
DEFAULT_RESPONSES_API_PREFIXES: List[str] = ["o1", "o3"]


class OpenAIAdapter(OpenAIChatCompletionsAdapter):
    """
    Adapter for OpenAI API.

    Direct access to OpenAI models including GPT-4, o3, and reasoning models.
    Automatically uses the correct API endpoint:
    - Chat Completions API for GPT models
    - Responses API for o3/o1 reasoning models

    Inherits from OpenAIChatCompletionsAdapter for Chat Completions support
    and adds Responses API handling for reasoning models.

    API Reference: https://platform.openai.com/docs/api-reference
    Default endpoint: https://api.openai.com/v1
    """

    provider_name = "OpenAI"
    # OpenAI: omit max_tokens to use model defaults
    default_max_tokens: Optional[int] = None

    def __init__(
        self,
        base_url: str,
        timeout: int = 60,
        max_retries: int = 3,
        api_key: Optional[str] = None,
        headers: Optional[dict[str, str]] = None,
        responses_api_prefixes: Optional[List[str]] = None,
        max_output_tokens: Optional[int] = None,
        max_completion_tokens: Optional[int] = None,
    ):
        """
        Initialize OpenAI adapter.

        Args:
            base_url: Base URL for API (default: https://api.openai.com/v1)
            timeout: Request timeout in seconds (default: 60)
            max_retries: Maximum retry attempts for transient failures (default: 3)
            api_key: OpenAI API key for authentication
            headers: Optional default headers to include in all requests
            responses_api_prefixes: Model prefixes that use Responses API (default: ["o1", "o3"])
            max_output_tokens: Maximum output tokens for Responses API requests (default: None)
            max_completion_tokens: Maximum tokens for Chat Completions API requests (default: None)
        """
        super().__init__(
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
            api_key=api_key,
            headers=headers,
        )
        self.responses_api_prefixes = (
            responses_api_prefixes
            if responses_api_prefixes is not None
            else DEFAULT_RESPONSES_API_PREFIXES
        )
        self.max_output_tokens = max_output_tokens
        self.max_completion_tokens = max_completion_tokens

    def _is_responses_api_model(self, model: str) -> bool:
        """
        Check if model requires the Responses API.

        Uses configurable prefix-based detection. Models starting with any
        of the configured prefixes are routed to the Responses API.

        Args:
            model: Model identifier to check

        Returns:
            True if model should use Responses API, False for Chat Completions
        """
        return any(
            model == prefix or model.startswith(f"{prefix}-")
            for prefix in self.responses_api_prefixes
        )

    def build_request(
        self, model: str, prompt: str
    ) -> Tuple[str, dict[str, str], dict]:
        """
        Build OpenAI API request.

        Uses Responses API for o3/o1 models, Chat Completions for others.

        Args:
            model: Model identifier (e.g., "gpt-4o", "o3-pro")
            prompt: The prompt to send

        Returns:
            Tuple of (endpoint, headers, body)
        """
        if not self._is_responses_api_model(model):
            # Use parent class for Chat Completions API (GPT models)
            endpoint, headers, body = super().build_request(model, prompt)

            # Add max_completion_tokens if configured (Chat Completions API parameter)
            if self.max_completion_tokens is not None:
                body["max_completion_tokens"] = self.max_completion_tokens

            return (endpoint, headers, body)

        # Responses API for o3/o1 reasoning models
        endpoint = "/responses"

        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }

        # Only include Authorization header when api_key is set
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        body: dict = {
            "model": model,
            "input": prompt,
        }

        # Include max_output_tokens if configured (Responses API parameter)
        if self.max_output_tokens is not None:
            body["max_output_tokens"] = self.max_output_tokens

        return (endpoint, headers, body)

    def parse_response(self, response_json: dict) -> str:
        """
        Parse OpenAI API response.

        Handles both Responses API and Chat Completions API formats.

        Args:
            response_json: Parsed JSON response from OpenAI

        Returns:
            Extracted response text

        Raises:
            KeyError: If response doesn't contain expected fields
            IndexError: If output/choices array is empty
        """
        # Responses API format (o3/o1 models) - check for "output" or "output_text" key
        if "output" in response_json or "output_text" in response_json:
            return self._parse_responses_api(response_json)

        # Chat Completions API format (GPT models) - use parent class
        if "choices" in response_json:
            return super().parse_response(response_json)

        raise KeyError(
            f"{self.provider_name} response missing both 'output' and 'choices' fields. "
            f"Received keys: {list(response_json.keys())}"
        )

    def _parse_responses_api(self, response_json: dict) -> str:
        """
        Parse Responses API format.

        Handles various output structures from OpenAI's Responses API,
        including output_text shortcut and structured output arrays.

        Args:
            response_json: Parsed JSON response

        Returns:
            Extracted text content

        Raises:
            IndexError: If output array is empty
            KeyError: If no text content can be extracted
        """
        # Check for output_text shortcut (common in newer API versions)
        if "output_text" in response_json:
            return response_json["output_text"]

        output = response_json.get("output", [])

        if len(output) == 0:
            raise IndexError(f"{self.provider_name} response has empty 'output' array")

        # Collect all text from output items
        texts: list[str] = []

        for item in output:
            item_type = item.get("type", "")

            if item_type == "message":
                # Handle message type with content array
                content = item.get("content", [])
                if isinstance(content, str):
                    texts.append(content)
                elif isinstance(content, list):
                    for content_item in content:
                        text = self._extract_text_from_content_item(content_item)
                        if text:
                            texts.append(text)

            elif item_type in ("output_text", "text"):
                # Direct text output
                if "text" in item:
                    texts.append(item["text"])

            elif "text" in item:
                # Fallback for items with text field
                texts.append(item["text"])

        if texts:
            result = "\n".join(texts)
            logger.debug(
                f"{self.provider_name} Responses API: extracted {len(texts)} text block(s)"
            )

            # Log warning if response status indicates incomplete or failed
            status = response_json.get("status", "unknown")
            if status == "incomplete":
                model = response_json.get("model", "unknown")
                incomplete_reason = response_json.get(
                    "incomplete_details", {}
                ).get("reason", "unknown")
                logger.warning(
                    f"{self.provider_name} response incomplete (status='incomplete', "
                    f"reason='{incomplete_reason}') for model {model}. "
                    f"Consider increasing max_output_tokens or checking input length."
                )
            elif status == "failed":
                model = response_json.get("model", "unknown")
                error_info = response_json.get("error", {})
                logger.warning(
                    f"{self.provider_name} response failed (status='failed') for model {model}. "
                    f"Error: {error_info}"
                )

            return result

        # Log warning with summarized structure for debugging
        output_types = [item.get("type", "unknown") for item in output[:5]]
        logger.warning(
            f"{self.provider_name} Responses API: could not extract text. "
            f"Output types: {output_types}, total items: {len(output)}"
        )

        raise KeyError(
            f"{self.provider_name} could not extract text from Responses API output. "
            f"Output contains {len(output)} items with types: {output_types}"
        )

    def _extract_text_from_content_item(
        self, content_item: Union[dict, str]
    ) -> Optional[str]:
        """
        Extract text from a content item in the Responses API output.

        Args:
            content_item: A content item (dict or str)

        Returns:
            Extracted text or None if not found
        """
        if isinstance(content_item, str):
            return content_item

        if isinstance(content_item, dict):
            content_type = content_item.get("type", "")

            # Handle both "text" and "output_text" types
            if content_type in ("text", "output_text"):
                return content_item.get("text", "")

            # Fallback: check for "text" field directly
            if "text" in content_item:
                return content_item["text"]

        return None
