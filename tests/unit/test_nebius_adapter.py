"""Tests for Nebius adapter."""
import pytest

from adapters.openrouter import NebiusAdapter, OpenAIChatCompletionsAdapter


class TestOpenAIChatCompletionsAdapter:
    """Tests for OpenAIChatCompletionsAdapter base class."""

    def test_base_class_defaults(self):
        """Test base class has correct defaults."""
        adapter = OpenAIChatCompletionsAdapter(
            base_url="http://localhost:8000", timeout=60
        )
        assert adapter.provider_name == "OpenAI-compatible"
        assert adapter.default_max_tokens is None

    def test_build_request_omits_max_tokens_when_none(self):
        """Test build_request omits max_tokens when default_max_tokens is None."""
        adapter = OpenAIChatCompletionsAdapter(
            base_url="http://localhost:8000", api_key="test-key", timeout=60
        )

        endpoint, headers, body = adapter.build_request(
            model="test-model", prompt="Hello"
        )

        assert "max_tokens" not in body

    def test_build_request_includes_max_tokens_when_set(self):
        """Test build_request includes max_tokens when default_max_tokens is set."""

        class CustomAdapter(OpenAIChatCompletionsAdapter):
            default_max_tokens = 2048

        adapter = CustomAdapter(
            base_url="http://localhost:8000", api_key="test-key", timeout=60
        )

        endpoint, headers, body = adapter.build_request(
            model="test-model", prompt="Hello"
        )

        assert body["max_tokens"] == 2048

    def test_build_request_omits_auth_when_no_api_key(self):
        """Test build_request omits Authorization header when api_key is None."""
        adapter = OpenAIChatCompletionsAdapter(
            base_url="http://localhost:8000", api_key=None, timeout=60
        )

        endpoint, headers, body = adapter.build_request(
            model="test-model", prompt="Hello"
        )

        assert "Authorization" not in headers

    def test_build_request_includes_auth_when_api_key_set(self):
        """Test build_request includes Authorization header when api_key is set."""
        adapter = OpenAIChatCompletionsAdapter(
            base_url="http://localhost:8000", api_key="sk-test-123", timeout=60
        )

        endpoint, headers, body = adapter.build_request(
            model="test-model", prompt="Hello"
        )

        assert headers["Authorization"] == "Bearer sk-test-123"

    def test_parse_response_uses_provider_name_in_errors(self):
        """Test parse_response uses provider_name in error messages."""

        class CustomAdapter(OpenAIChatCompletionsAdapter):
            provider_name = "CustomProvider"

        adapter = CustomAdapter(
            base_url="http://localhost:8000", timeout=60
        )

        with pytest.raises(KeyError) as exc_info:
            adapter.parse_response({"error": "bad request"})

        assert "CustomProvider" in str(exc_info.value)


class TestNebiusAdapter:
    """Tests for NebiusAdapter."""

    def test_adapter_initialization(self):
        """Test adapter initializes correctly."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1",
            api_key="test-key",
            timeout=600,
        )
        assert adapter.base_url == "https://api.tokenfactory.nebius.com/v1"
        assert adapter.api_key == "test-key"
        assert adapter.timeout == 600

    def test_provider_name(self):
        """Test Nebius adapter has correct provider_name."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1", timeout=60
        )
        assert adapter.provider_name == "Nebius"

    def test_default_max_tokens_is_none(self):
        """Test Nebius adapter does not set max_tokens (uses model defaults)."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1", timeout=60
        )
        assert adapter.default_max_tokens is None

    def test_build_request_omits_max_tokens(self):
        """Test build_request does not include max_tokens for Nebius."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1",
            api_key="test-key",
            timeout=60,
        )

        endpoint, headers, body = adapter.build_request(
            model="meta-llama/Llama-3.3-70B-Instruct", prompt="What is 2+2?"
        )

        assert endpoint == "/chat/completions"
        assert "max_tokens" not in body
        assert body["model"] == "meta-llama/Llama-3.3-70B-Instruct"
        assert body["messages"] == [{"role": "user", "content": "What is 2+2?"}]
        assert body["stream"] is False

    def test_build_request_with_api_key(self):
        """Test build_request includes Authorization header with api_key."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1",
            api_key="nebius-test-key",
            timeout=60,
        )

        endpoint, headers, body = adapter.build_request(
            model="test-model", prompt="test"
        )

        assert headers["Authorization"] == "Bearer nebius-test-key"
        assert headers["Content-Type"] == "application/json"

    def test_build_request_without_api_key(self):
        """Test build_request omits Authorization header when api_key is None."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1",
            api_key=None,
            timeout=60,
        )

        endpoint, headers, body = adapter.build_request(
            model="test-model", prompt="test"
        )

        assert "Authorization" not in headers

    def test_parse_response_extracts_content(self):
        """Test parse_response extracts message content from OpenAI format."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1", timeout=60
        )

        response_json = {
            "id": "chatcmpl-123",
            "model": "meta-llama/Llama-3.3-70B-Instruct",
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

    def test_parse_response_handles_missing_choices(self):
        """Test parse_response raises error with Nebius provider name."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1", timeout=60
        )

        with pytest.raises(KeyError) as exc_info:
            adapter.parse_response({"id": "123", "model": "test"})

        assert "Nebius" in str(exc_info.value)
        assert "choices" in str(exc_info.value).lower()

    def test_parse_response_handles_empty_choices(self):
        """Test parse_response raises error if choices is empty."""
        adapter = NebiusAdapter(
            base_url="https://api.tokenfactory.nebius.com/v1", timeout=60
        )

        with pytest.raises(IndexError) as exc_info:
            adapter.parse_response({"choices": []})

        assert "Nebius" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_invoke_success(self):
        """Test successful invocation with mocked HTTP client."""
        from unittest.mock import AsyncMock, Mock, patch

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response from Nebius"}}]
        }

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)

        with patch("httpx.AsyncClient", return_value=mock_client):
            adapter = NebiusAdapter(
                base_url="https://api.tokenfactory.nebius.com/v1",
                api_key="nebius-key",
                timeout=60,
            )
            result = await adapter.invoke(
                prompt="Hello", model="meta-llama/Llama-3.3-70B-Instruct"
            )

            assert result == "Response from Nebius"
            mock_client.post.assert_called_once()

            # Verify max_tokens was NOT included in request
            call_args = mock_client.post.call_args
            request_body = call_args[1]["json"]
            assert "max_tokens" not in request_body
