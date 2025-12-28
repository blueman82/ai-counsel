"""Tests for OpenAI adapter.

API References:
- Chat Completions API: https://platform.openai.com/docs/api-reference/chat
- Responses API (o3/o1): https://platform.openai.com/docs/api-reference/responses
"""
import pytest

from adapters.openai import OpenAIAdapter


class TestOpenAIAdapter:
    """Tests for OpenAIAdapter.

    Tests cover both API formats:
    - Chat Completions API (/chat/completions) for GPT models
    - Responses API (/responses) for o3/o1 reasoning models
    """

    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1", api_key="sk-test-123", timeout=90
        )
        assert adapter.base_url == "https://api.openai.com/v1"
        assert adapter.api_key == "sk-test-123"
        assert adapter.timeout == 90
        assert adapter.provider_name == "OpenAI"

    def test_adapter_initialization_without_api_key(self):
        """Test adapter can be initialized without API key (will fail on request)."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", timeout=60)
        assert adapter.base_url == "https://api.openai.com/v1"
        assert adapter.api_key is None

    def test_is_responses_api_model_o3(self):
        """Test that o3 models are detected as Responses API models."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        assert adapter._is_responses_api_model("o3") is True
        assert adapter._is_responses_api_model("o3-pro") is True
        assert adapter._is_responses_api_model("o3-mini") is True
        assert adapter._is_responses_api_model("o3-deep-research") is True

    def test_is_responses_api_model_o1(self):
        """Test that o1 models are detected as Responses API models."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        assert adapter._is_responses_api_model("o1") is True
        assert adapter._is_responses_api_model("o1-pro") is True
        assert adapter._is_responses_api_model("o1-mini") is True

    def test_is_responses_api_model_gpt(self):
        """Test that GPT models are NOT detected as Responses API models."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        assert adapter._is_responses_api_model("gpt-4") is False
        assert adapter._is_responses_api_model("gpt-4o") is False
        assert adapter._is_responses_api_model("gpt-4-turbo") is False
        assert adapter._is_responses_api_model("gpt-3.5-turbo") is False

    def test_is_responses_api_model_boundaries(self):
        """Boundary checks for Responses API model detection."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        assert adapter._is_responses_api_model("o1") is True
        assert adapter._is_responses_api_model("o1-pro") is True
        assert adapter._is_responses_api_model("gpt-4o1") is False
        assert adapter._is_responses_api_model("co3") is False

    def test_build_request_chat_completions(self):
        """Test build_request for GPT models uses Chat Completions API."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1", api_key="sk-test-key-123"
        )

        endpoint, headers, body = adapter.build_request(
            model="gpt-4o", prompt="What is 2+2?"
        )

        assert endpoint == "/chat/completions"
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer sk-test-key-123"
        assert body["model"] == "gpt-4o"
        assert body["messages"] == [{"role": "user", "content": "What is 2+2?"}]
        assert body["stream"] is False

    def test_build_request_responses_api(self):
        """Test build_request for o3 models uses Responses API."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1", api_key="sk-test-key-123"
        )

        endpoint, headers, body = adapter.build_request(
            model="o3-pro", prompt="Solve this problem"
        )

        assert endpoint == "/responses"
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer sk-test-key-123"
        assert body["model"] == "o3-pro"
        assert body["input"] == "Solve this problem"
        assert "messages" not in body

    def test_build_request_without_api_key_omits_auth_header(self):
        """Test build_request omits Authorization header when api_key is None."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key=None)

        # Test for Chat Completions API
        endpoint, headers, body = adapter.build_request(model="gpt-4o", prompt="test")
        assert "Authorization" not in headers

        # Test for Responses API
        endpoint, headers, body = adapter.build_request(model="o3-pro", prompt="test")
        assert "Authorization" not in headers

    def test_parse_response_chat_completions(self):
        """Test parse_response extracts content from Chat Completions format."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {
            "id": "chatcmpl-123",
            "model": "gpt-4o",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "The answer is 4."},
                    "finish_reason": "stop",
                }
            ],
        }

        result = adapter.parse_response(response_json)
        assert result == "The answer is 4."

    def test_parse_response_responses_api_output_text(self):
        """Test parse_response with output_text shortcut."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {
            "id": "resp-123",
            "model": "o3-pro",
            "output_text": "The solution is X.",
            "output": [],
        }

        result = adapter.parse_response(response_json)
        assert result == "The solution is X."

    def test_parse_response_responses_api_message_content(self):
        """Test parse_response with message content structure."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {
            "id": "resp-123",
            "model": "o3-pro",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "text", "text": "Here is the answer."}],
                }
            ],
        }

        result = adapter.parse_response(response_json)
        assert result == "Here is the answer."

    def test_parse_response_responses_api_output_text_type(self):
        """Test parse_response with output_text type in content."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {
            "id": "resp-123",
            "model": "o3",
            "output": [
                {
                    "type": "message",
                    "content": [{"type": "output_text", "text": "Output text here."}],
                }
            ],
        }

        result = adapter.parse_response(response_json)
        assert result == "Output text here."

    def test_parse_response_responses_api_multiple_text_blocks(self):
        """Test parse_response concatenates multiple text blocks."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {
            "id": "resp-123",
            "model": "o3",
            "output": [
                {
                    "type": "message",
                    "content": [
                        {"type": "text", "text": "First part."},
                        {"type": "text", "text": "Second part."},
                    ],
                }
            ],
        }

        result = adapter.parse_response(response_json)
        assert result == "First part.\nSecond part."

    def test_parse_response_responses_api_string_content(self):
        """Test parse_response handles string content directly."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {
            "id": "resp-123",
            "model": "o3",
            "output": [{"type": "message", "content": "Direct string content."}],
        }

        result = adapter.parse_response(response_json)
        assert result == "Direct string content."

    def test_parse_response_handles_missing_both_keys(self):
        """Test parse_response raises error if both output and choices missing."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {"id": "resp-123", "model": "unknown"}

        with pytest.raises(KeyError) as exc_info:
            adapter.parse_response(response_json)

        assert "output" in str(exc_info.value).lower()
        assert "choices" in str(exc_info.value).lower()

    def test_parse_response_handles_empty_output(self):
        """Test parse_response raises error if output is empty."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {"output": []}

        with pytest.raises(IndexError):
            adapter.parse_response(response_json)

    def test_parse_response_handles_empty_choices(self):
        """Test parse_response raises error if choices is empty."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        response_json = {"choices": []}

        with pytest.raises(IndexError):
            adapter.parse_response(response_json)

    @pytest.mark.asyncio
    async def test_invoke_success_chat_completions(self):
        """Test successful invocation with Chat Completions API."""
        from unittest.mock import AsyncMock, Mock, patch

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Test response from GPT"}}]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            adapter = OpenAIAdapter(
                base_url="https://api.openai.com/v1",
                api_key="sk-test-key",
                timeout=60,
            )
            result = await adapter.invoke(prompt="Say hello", model="gpt-4o")

            assert result == "Test response from GPT"
            mock_client.post.assert_called_once()

            # Verify the request was built correctly
            call_args = mock_client.post.call_args
            assert "/chat/completions" in call_args[0][0]
            assert call_args[1]["headers"]["Authorization"] == "Bearer sk-test-key"

    @pytest.mark.asyncio
    async def test_invoke_success_responses_api(self):
        """Test successful invocation with Responses API."""
        from unittest.mock import AsyncMock, Mock, patch

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "output_text": "Test response from o3"
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            adapter = OpenAIAdapter(
                base_url="https://api.openai.com/v1",
                api_key="sk-test-key",
                timeout=60,
            )
            result = await adapter.invoke(prompt="Solve this", model="o3-pro")

            assert result == "Test response from o3"
            mock_client.post.assert_called_once()

            # Verify the request was built correctly for Responses API
            call_args = mock_client.post.call_args
            assert "/responses" in call_args[0][0]
            assert call_args[1]["json"]["input"] == "Solve this"


class TestOpenAIAdapterConfigurableRouting:
    """Tests for configurable Responses API routing."""

    def test_default_responses_api_prefixes(self):
        """Test adapter uses default prefixes when none specified."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        assert adapter.responses_api_prefixes == ["o1", "o3"]

    def test_custom_responses_api_prefixes(self):
        """Test adapter uses custom prefixes when specified."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            responses_api_prefixes=["o1", "o3", "o4"],
        )

        assert adapter.responses_api_prefixes == ["o1", "o3", "o4"]
        # o4 models should now be routed to Responses API
        assert adapter._is_responses_api_model("o4-preview") is True
        # Default o1/o3 still work
        assert adapter._is_responses_api_model("o3-pro") is True

    def test_empty_responses_api_prefixes_routes_all_to_chat(self):
        """Test empty prefixes list routes all models to Chat Completions."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            responses_api_prefixes=[],
        )

        # All models should use Chat Completions when prefixes is empty
        assert adapter._is_responses_api_model("o3-pro") is False
        assert adapter._is_responses_api_model("o1") is False
        assert adapter._is_responses_api_model("gpt-4o") is False

    def test_custom_prefix_routing(self):
        """Test routing with completely custom prefixes."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            responses_api_prefixes=["custom-reasoning"],
        )

        # Only custom prefix routes to Responses API
        assert adapter._is_responses_api_model("custom-reasoning-v1") is True
        assert adapter._is_responses_api_model("o3-pro") is False
        assert adapter._is_responses_api_model("gpt-4o") is False


class TestOpenAIAdapterMaxOutputTokens:
    """Tests for max_output_tokens configuration."""

    def test_default_max_output_tokens_is_none(self):
        """Test adapter has no max_output_tokens by default."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        assert adapter.max_output_tokens is None

    def test_custom_max_output_tokens(self):
        """Test adapter accepts custom max_output_tokens."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_output_tokens=16384,
        )

        assert adapter.max_output_tokens == 16384

    def test_responses_api_request_includes_max_output_tokens(self):
        """Test Responses API request includes max_output_tokens when configured."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_output_tokens=8192,
        )

        endpoint, headers, body = adapter.build_request(
            model="o3-pro", prompt="Solve this"
        )

        assert endpoint == "/responses"
        assert body["max_output_tokens"] == 8192

    def test_responses_api_request_omits_max_output_tokens_when_none(self):
        """Test Responses API request omits max_output_tokens when not configured."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_output_tokens=None,
        )

        endpoint, headers, body = adapter.build_request(
            model="o3-pro", prompt="Solve this"
        )

        assert endpoint == "/responses"
        assert "max_output_tokens" not in body

    def test_chat_completions_unaffected_by_max_output_tokens(self):
        """Test Chat Completions API is not affected by max_output_tokens setting."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_output_tokens=8192,
        )

        endpoint, headers, body = adapter.build_request(
            model="gpt-4o", prompt="What is 2+2?"
        )

        assert endpoint == "/chat/completions"
        # max_output_tokens is for Responses API only
        assert "max_output_tokens" not in body


class TestOpenAIAdapterMaxCompletionTokens:
    """Tests for max_completion_tokens configuration (Chat Completions API)."""

    def test_default_max_completion_tokens_is_none(self):
        """Test adapter has no max_completion_tokens by default."""
        adapter = OpenAIAdapter(base_url="https://api.openai.com/v1", api_key="sk-test")

        assert adapter.max_completion_tokens is None

    def test_custom_max_completion_tokens(self):
        """Test adapter accepts custom max_completion_tokens."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_completion_tokens=4096,
        )

        assert adapter.max_completion_tokens == 4096

    def test_chat_completions_request_includes_max_completion_tokens(self):
        """Test Chat Completions API request includes max_completion_tokens when configured."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_completion_tokens=4096,
        )

        endpoint, headers, body = adapter.build_request(
            model="gpt-4o", prompt="What is 2+2?"
        )

        assert endpoint == "/chat/completions"
        assert body["max_completion_tokens"] == 4096

    def test_chat_completions_request_omits_max_completion_tokens_when_none(self):
        """Test Chat Completions API request omits max_completion_tokens when not configured."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_completion_tokens=None,
        )

        endpoint, headers, body = adapter.build_request(
            model="gpt-4o", prompt="What is 2+2?"
        )

        assert endpoint == "/chat/completions"
        assert "max_completion_tokens" not in body

    def test_responses_api_unaffected_by_max_completion_tokens(self):
        """Test Responses API is not affected by max_completion_tokens setting."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_completion_tokens=4096,
        )

        endpoint, headers, body = adapter.build_request(
            model="o3-pro", prompt="Solve this problem"
        )

        assert endpoint == "/responses"
        # max_completion_tokens is for Chat Completions API only
        assert "max_completion_tokens" not in body

    def test_both_token_limits_configured(self):
        """Test both max_output_tokens and max_completion_tokens can be set."""
        adapter = OpenAIAdapter(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            max_output_tokens=16384,
            max_completion_tokens=4096,
        )

        # Chat Completions uses max_completion_tokens
        endpoint, headers, body = adapter.build_request(
            model="gpt-4o", prompt="Hello"
        )
        assert endpoint == "/chat/completions"
        assert body["max_completion_tokens"] == 4096
        assert "max_output_tokens" not in body

        # Responses API uses max_output_tokens
        endpoint, headers, body = adapter.build_request(
            model="o3-pro", prompt="Hello"
        )
        assert endpoint == "/responses"
        assert body["max_output_tokens"] == 16384
        assert "max_completion_tokens" not in body
