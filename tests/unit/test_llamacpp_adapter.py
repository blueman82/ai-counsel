"""Unit tests for LlamaCppAdapter.

llama.cpp is a CLI tool for running LLMs locally with unique output format.
Unlike other adapters, llama.cpp outputs include:
- Model loading information
- Sampling parameters
- Token generation stats (tokens/s, timing)
- Perplexity information
- The actual response text mixed with metadata

Test cases cover:
1. Initialization with proper defaults
2. Output parsing to extract response from verbose output
3. Handling various llama.cpp output formats
4. Error handling for malformed output
5. Context and prompt integration
"""
import asyncio
from unittest.mock import AsyncMock, Mock, patch

import pytest

from adapters.llamacpp import LlamaCppAdapter


class TestLlamaCppAdapter:
    """Tests for LlamaCppAdapter."""

    def test_should_initialize_with_correct_defaults_when_created(self):
        """Test adapter initializes with correct command and timeout."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"], timeout=120)
        assert adapter.command == "llama-cli"
        assert adapter.timeout == 120
        assert adapter.args == ["-m", "{model}", "-p", "{prompt}"]

    def test_should_require_args_when_initializing(self):
        """Test adapter requires args parameter from config."""
        with pytest.raises(ValueError) as exc_info:
            LlamaCppAdapter()

        assert "args must be provided" in str(exc_info.value)

    def test_should_extract_response_when_parsing_verbose_output(self):
        """Test parsing extracts model response from verbose llama.cpp output."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        # Typical llama.cpp output includes metadata before/after response
        raw_output = """
llama_model_loader: loaded meta data with 20 key-value pairs and 291 tensors
llm_load_print_meta: model type = 7B
llm_load_print_meta: BOS token = 1 '<s>'
llm_load_print_meta: EOS token = 2 '</s>'
llama_new_context_with_model: n_ctx = 512

sampling: repeat_last_n = 64, repeat_penalty = 1.100
generate: n_ctx = 512, n_batch = 512, n_predict = 128, n_keep = 0

The answer to your question is 42. This is based on mathematical reasoning and logical deduction.

llama_print_timings:        load time =   234.56 ms
llama_print_timings:      sample time =    12.34 ms /   128 runs
llama_print_timings: prompt eval time =    45.67 ms /    10 tokens
llama_print_timings:        eval time =   890.12 ms /   128 tokens
llama_print_timings:       total time =  1234.56 ms
        """

        result = adapter.parse_output(raw_output)

        # Should extract only the actual response
        assert "The answer to your question is 42" in result
        assert "mathematical reasoning" in result
        # Should NOT include metadata
        assert "llama_model_loader" not in result
        assert "llm_load_print_meta" not in result
        assert "llama_print_timings" not in result
        assert "sampling:" not in result

    def test_should_handle_multiline_response_when_parsing_output(self):
        """Test parsing preserves multiline responses."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        raw_output = """
llama_new_context_with_model: n_ctx = 512
sampling: repeat_last_n = 64

Here is my detailed answer:

1. First point with explanation
2. Second point with more details
3. Third point concluding the argument

This covers all aspects of your question.

llama_print_timings:        load time =   123.45 ms
        """

        result = adapter.parse_output(raw_output)

        # Should preserve multiline structure
        assert "Here is my detailed answer:" in result
        assert "1. First point" in result
        assert "2. Second point" in result
        assert "3. Third point" in result
        assert "This covers all aspects" in result
        # No metadata
        assert "llama_new_context" not in result
        assert "llama_print_timings" not in result

    def test_should_extract_response_when_output_has_no_timings(self):
        """Test parsing works when llama.cpp output lacks timing info."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        raw_output = """
llama_model_loader: loaded meta data
sampling: repeat_last_n = 64

This is a simple response without timing information at the end.
        """

        result = adapter.parse_output(raw_output)

        assert "This is a simple response" in result
        assert "llama_model_loader" not in result
        assert "sampling:" not in result

    def test_should_handle_empty_lines_when_parsing_output(self):
        """Test parsing handles empty lines gracefully."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        raw_output = """
llama_new_context_with_model: n_ctx = 512


Response with empty lines above and below.


llama_print_timings: total time = 100 ms
        """

        result = adapter.parse_output(raw_output)

        assert "Response with empty lines" in result
        # Should preserve internal empty lines but strip leading/trailing
        assert result.strip() == "Response with empty lines above and below."

    def test_should_strip_whitespace_when_parsing_output(self):
        """Test parsing strips leading and trailing whitespace."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        raw_output = """
llama_new_context_with_model: n_ctx = 512

    Response with indentation and trailing spaces.

llama_print_timings: total time = 100 ms
        """

        result = adapter.parse_output(raw_output)

        # Should strip outer whitespace but preserve sentence structure
        assert result.strip() == "Response with indentation and trailing spaces."

    def test_should_handle_response_only_output_when_parsing(self):
        """Test parsing handles output with minimal metadata."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        # Some llama.cpp builds may have minimal output
        raw_output = "Just the response text without metadata."

        result = adapter.parse_output(raw_output)

        assert result == "Just the response text without metadata."

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_should_invoke_successfully_when_process_succeeds(
        self, mock_subprocess
    ):
        """Test successful CLI invocation."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(
                b"""
llama_model_loader: loaded meta data
sampling: repeat_last_n = 64

The answer is 42.

llama_print_timings: total time = 100 ms
            """,
                b"",
            )
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])
        result = await adapter.invoke(
            prompt="What is the answer?", model="/path/to/model.gguf"
        )

        assert result == "The answer is 42."
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_should_raise_timeout_error_when_process_times_out(
        self, mock_subprocess
    ):
        """Test timeout handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(side_effect=asyncio.TimeoutError())
        mock_subprocess.return_value = mock_process

        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"], timeout=1)

        with pytest.raises(TimeoutError) as exc_info:
            await adapter.invoke("test prompt", "/path/to/model.gguf")

        assert "timed out" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_should_raise_runtime_error_when_process_fails(self, mock_subprocess):
        """Test process error handling."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"error: failed to load model")
        )
        mock_process.returncode = 1
        mock_subprocess.return_value = mock_process

        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        with pytest.raises(RuntimeError) as exc_info:
            await adapter.invoke("test prompt", "/path/to/model.gguf")

        assert "failed" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    @patch("adapters.base.asyncio.create_subprocess_exec")
    async def test_should_include_context_when_provided(self, mock_subprocess):
        """Test context is prepended to prompt."""
        mock_process = Mock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Response with context.", b"")
        )
        mock_process.returncode = 0
        mock_subprocess.return_value = mock_process

        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])
        result = await adapter.invoke(
            prompt="Answer this:",
            model="/path/to/model.gguf",
            context="Previous context here.",
        )

        # Verify subprocess was called with combined prompt
        call_args = mock_subprocess.call_args
        combined_prompt = None
        for arg in call_args[0]:
            if "Previous context" in arg and "Answer this:" in arg:
                combined_prompt = arg
                break

        assert combined_prompt is not None
        assert "Previous context here." in combined_prompt
        assert "Answer this:" in combined_prompt
        assert result == "Response with context."

    def test_should_handle_response_with_code_blocks_when_parsing(self):
        """Test parsing preserves code blocks in response."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        raw_output = """
llama_new_context_with_model: n_ctx = 512

Here's a code example:

```python
def hello():
    print("Hello, world!")
```

This demonstrates the concept.

llama_print_timings: total time = 200 ms
        """

        result = adapter.parse_output(raw_output)

        assert "Here's a code example:" in result
        assert "```python" in result
        assert "def hello():" in result
        assert "This demonstrates the concept." in result
        assert "llama_print_timings" not in result

    def test_should_handle_special_characters_when_parsing_output(self):
        """Test parsing preserves special characters in response."""
        adapter = LlamaCppAdapter(args=["-m", "{model}", "-p", "{prompt}"])

        raw_output = """
llama_new_context_with_model: n_ctx = 512

Response with special chars: @#$%^&*()
Also includes: "quotes" and 'apostrophes'
Mathematical symbols: ∑ ∫ √ π

llama_print_timings: total time = 100 ms
        """

        result = adapter.parse_output(raw_output)

        assert "@#$%^&*()" in result
        assert '"quotes"' in result
        assert "'apostrophes'" in result
        assert "∑ ∫ √ π" in result
        assert "llama_print_timings" not in result
