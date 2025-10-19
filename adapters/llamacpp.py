"""llama.cpp CLI adapter.

llama.cpp is a fast, lightweight LLM inference engine for running models locally.
It outputs verbose metadata along with the actual model response, requiring
custom parsing logic to extract just the response text.

Typical output format:
    llama_model_loader: loaded meta data with N key-value pairs
    llm_load_print_meta: model type = 7B
    llama_new_context_with_model: n_ctx = 512
    sampling: repeat_last_n = 64, repeat_penalty = 1.100

    [Actual model response here]

    llama_print_timings: load time = X ms
    llama_print_timings: sample time = Y ms
    llama_print_timings: eval time = Z ms
"""
from adapters.base import BaseCLIAdapter


class LlamaCppAdapter(BaseCLIAdapter):
    """Adapter for llama.cpp CLI tool (llama-cli)."""

    def __init__(
        self,
        command: str = "llama-cli",
        args: list[str] | None = None,
        timeout: int = 120,
    ):
        """
        Initialize llama.cpp adapter.

        Args:
            command: Command to execute (default: "llama-cli")
            args: List of argument templates (from config.yaml)
            timeout: Timeout in seconds (default: 120, as local inference can be slow)

        Raises:
            ValueError: If args is not provided
        """
        if args is None:
            raise ValueError("args must be provided from config.yaml")
        super().__init__(command=command, args=args, timeout=timeout)

    def parse_output(self, raw_output: str) -> str:
        """
        Parse llama.cpp CLI output to extract model response.

        llama.cpp outputs verbose metadata before and after the actual response.
        This parser identifies and removes:
        - llama_model_loader lines (model loading info)
        - llm_load_print_meta lines (model metadata)
        - llama_new_context_with_model lines (context setup)
        - sampling: lines (sampling parameters)
        - generate: lines (generation settings)
        - llama_print_timings lines (performance metrics)

        The actual model response is typically the text between these metadata blocks.

        Args:
            raw_output: Raw stdout from llama.cpp CLI

        Returns:
            Extracted model response with metadata removed
        """
        lines = raw_output.strip().split("\n")

        # Metadata prefixes to filter out
        metadata_prefixes = [
            "llama_model_loader:",
            "llm_load_print_meta:",
            "llama_new_context_with_model:",
            "llama_print_timings:",
            "sampling:",
            "generate:",
            "llm_load_tensors:",
            "llama_kv_cache_init:",
            "system_info:",
        ]

        # Filter out metadata lines
        response_lines = []
        for line in lines:
            # Check if line starts with any metadata prefix
            is_metadata = any(
                line.strip().startswith(prefix) for prefix in metadata_prefixes
            )

            if not is_metadata:
                response_lines.append(line)

        # Join and strip the result
        response = "\n".join(response_lines).strip()
        return response
