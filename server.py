"""AI Counsel MCP Server."""
import asyncio
import logging
from pathlib import Path
import sys
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
import json

from models.config import load_config
from models.schema import DeliberateRequest
from adapters import create_adapter
from deliberation.engine import DeliberationEngine
from deliberation.query_engine import QueryEngine
from decision_graph.storage import DecisionGraphStorage

# Get the absolute path to the server directory
SERVER_DIR = Path(__file__).parent.absolute()

# Configure logging to file to avoid stdio interference
log_file = SERVER_DIR / "mcp_server.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr),  # Explicitly use stderr
    ],
)
logger = logging.getLogger(__name__)


# Initialize server
app = Server("ai-counsel")


# Load configuration with absolute path
try:
    config_path = SERVER_DIR / "config.yaml"
    logger.info(f"Loading config from: {config_path}")
    config = load_config(str(config_path))
    logger.info("Configuration loaded successfully")
except Exception as e:
    logger.error(f"Failed to load config: {e}", exc_info=True)
    raise


# Create adapters - prefer new 'adapters' section, fallback to legacy 'cli_tools'
adapters = {}
adapter_sources = []

# Try new adapters section first (preferred)
if hasattr(config, 'adapters') and config.adapters:
    adapter_sources.append(('adapters', config.adapters))

# Fallback to legacy cli_tools for backward compatibility
if hasattr(config, 'cli_tools') and config.cli_tools:
    adapter_sources.append(('cli_tools', config.cli_tools))

for source_name, adapter_configs in adapter_sources:
    for cli_name, cli_config in adapter_configs.items():
        # Skip if already loaded from preferred source
        if cli_name in adapters:
            logger.debug(f"Adapter '{cli_name}' already loaded from preferred source, skipping {source_name}")
            continue

        try:
            adapters[cli_name] = create_adapter(cli_name, cli_config)
            logger.info(f"Initialized adapter: {cli_name} (from {source_name})")
        except Exception as e:
            logger.error(f"Failed to create adapter for {cli_name}: {e}")


# Create engine with config for convergence detection
engine = DeliberationEngine(adapters=adapters, config=config, server_dir=SERVER_DIR)

# Recommended models for each adapter (CLI tools and HTTP services)
# Note: ollama, lmstudio, and llamacpp are excluded since users can load arbitrary models
RECOMMENDED_MODELS = {
    "claude": [
        "sonnet",
        "opus",
        "haiku",
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-1-20250805",
    ],
    "codex": ["gpt-5-codex", "o3"],
    "droid": ["claude-sonnet-4-5-20250929", "gpt-5-codex", "claude-opus-4-1-20250805"],
    "gemini": ["gemini-2.5-pro", "gemini-2.0-flash"],
    "openrouter": [
        "anthropic/claude-3.5-sonnet",
        "openai/gpt-4",
        "meta-llama/llama-3.2-90b",
    ],
}


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    tools = [
        Tool(
            name="deliberate",
            description=(
                "Initiate true deliberative consensus where AI models debate and "
                "refine positions across multiple rounds. Models see each other's "
                "responses and can adjust their reasoning. Supports both CLI tools "
                "(claude, codex, droid, gemini, llamacpp) and HTTP services (ollama, lmstudio, openrouter). "
                "Use for critical decisions, architecture choices, or complex technical debates.\n\n"
                "Example participants:\n"
                '  [{"cli": "claude", "model": "sonnet"}, '
                '{"cli": "llamacpp", "model": "/path/to/llama-2-7b.Q4_K_M.gguf"}]\n\n'
                "Recommended models by adapter:\n"
                "  - claude: 'sonnet', 'opus', 'haiku'\n"
                "  - codex: 'gpt-5-codex', 'o3'\n"
                "  - droid: 'claude-sonnet-4-5-20250929', 'gpt-5-codex'\n"
                "  - gemini: 'gemini-2.5-pro'\n"
                "  - llamacpp: '/path/to/model.gguf' (path to local .gguf model file)\n"
                "  - ollama: 'llama2', 'mistral', 'codellama', 'qwen'\n"
                "  - lmstudio: 'local-model' (model names vary based on loaded models)\n"
                "  - openrouter: 'anthropic/claude-3.5-sonnet', 'openai/gpt-4' (requires API key)"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question or proposal for the models to deliberate on",
                        "minLength": 10,
                    },
                    "participants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "cli": {
                                    "type": "string",
                                    "enum": [
                                        "claude",
                                        "codex",
                                        "droid",
                                        "gemini",
                                        "llamacpp",
                                        "ollama",
                                        "lmstudio",
                                        "openrouter",
                                    ],
                                    "description": "Adapter to use (CLI tools or HTTP services)",
                                },
                                "model": {
                                    "type": "string",
                                    "description": "Model identifier (e.g., 'claude-3-5-sonnet-20241022', 'gpt-4')",
                                },
                                "stance": {
                                    "type": "string",
                                    "enum": ["neutral", "for", "against"],
                                    "default": "neutral",
                                    "description": "Stance for this participant",
                                },
                            },
                            "required": ["cli", "model"],
                        },
                        "minItems": 2,
                        "description": "List of AI participants (minimum 2)",
                    },
                    "rounds": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 2,
                        "description": "Number of deliberation rounds (1-5)",
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["quick", "conference"],
                        "default": "quick",
                        "description": "quick = single round opinions, conference = multi-round deliberation",
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional additional context (code snippets, requirements, etc.)",
                    },
                },
                "required": ["question", "participants"],
            },
        )
    ]

    # Add decision graph tools if enabled
    if hasattr(config, "decision_graph") and config.decision_graph.enabled:
        tools.extend([
            Tool(
                name="query_decisions",
                description=(
                    "Search and analyze past deliberations in the decision graph memory. "
                    "Find similar decisions by semantic meaning, identify contradictions, "
                    "or trace how decisions evolved over time."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query_text": {
                            "type": "string",
                            "description": "Query text to search for similar decisions",
                        },
                        "find_contradictions": {
                            "type": "boolean",
                            "default": False,
                            "description": "Find contradictions in decision history instead of searching",
                        },
                        "decision_id": {
                            "type": "string",
                            "description": "Trace evolution of a specific decision by ID",
                        },
                        "limit": {
                            "type": "integer",
                            "default": 5,
                            "minimum": 1,
                            "maximum": 20,
                            "description": "Maximum number of results to return",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["summary", "detailed", "json"],
                            "default": "summary",
                            "description": "Output format",
                        },
                    },
                },
            ),
            Tool(
                name="analyze_decisions",
                description=(
                    "Analyze aggregated patterns from past deliberations. "
                    "Get voting patterns, convergence statistics, and participation metrics."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "participant": {
                            "type": "string",
                            "description": "Optional: filter analysis for a specific participant",
                        },
                    },
                },
            ),
        ])

    return tools


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """
    Handle tool calls from MCP client.

    Args:
        name: Tool name ("deliberate", "query_decisions", "analyze_decisions")
        arguments: Tool arguments as dict

    Returns:
        List of TextContent with JSON response
    """
    logger.info(f"Tool call received: {name} with arguments: {arguments}")

    if name == "query_decisions":
        return await handle_query_decisions(arguments)
    elif name == "analyze_decisions":
        return await handle_analyze_decisions(arguments)
    elif name != "deliberate":
        error_msg = f"Unknown tool: {name}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    try:
        # Validate and parse request
        logger.info("Validating request parameters...")
        request = DeliberateRequest(**arguments)
        logger.info(
            f"Request validated. Starting deliberation: {request.question[:50]}..."
        )

        # Validate model choices and warn if non-recommended
        for participant in request.participants:
            cli = participant.cli
            model = participant.model

            if cli in RECOMMENDED_MODELS:
                recommended = RECOMMENDED_MODELS[cli]
                if model not in recommended:
                    logger.warning(
                        f"Model '{model}' not in recommended list for {cli}. "
                        f"Recommended models: {', '.join(recommended)}. "
                        f"Proceeding anyway - if this fails, try a recommended model."
                    )

        # Execute deliberation
        result = await engine.execute(request)
        logger.info(
            f"Deliberation complete: {result.rounds_completed} rounds, status: {result.status}"
        )

        # Truncate full_debate for MCP response if needed (to avoid token limit)
        max_rounds = getattr(config, "mcp", {}).get("max_rounds_in_response", 3)
        result_dict = result.model_dump()

        if len(result.full_debate) > max_rounds:
            total_rounds = len(result.full_debate)
            # Convert RoundResponse objects to dicts for the truncated slice
            result_dict["full_debate"] = [
                r.model_dump() if hasattr(r, "model_dump") else r
                for r in result.full_debate[-max_rounds:]
            ]
            result_dict["full_debate_truncated"] = True
            result_dict["total_rounds"] = total_rounds
            logger.info(
                f"Truncated full_debate from {total_rounds} to last {max_rounds} rounds for MCP response"
            )
        else:
            result_dict["full_debate_truncated"] = False

        # Serialize result
        result_json = json.dumps(result_dict, indent=2)
        logger.info(f"Result serialized, length: {len(result_json)} chars")

        # Return result as TextContent
        response = [TextContent(type="text", text=result_json)]
        logger.info("Response prepared successfully")
        return response

    except Exception as e:
        logger.error(f"Error in deliberation: {type(e).__name__}: {e}", exc_info=True)
        error_response = {
            "error": str(e),
            "error_type": type(e).__name__,
            "status": "failed",
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]


async def handle_query_decisions(arguments: dict) -> list[TextContent]:
    """Handle query_decisions tool call."""
    try:
        db_path = Path(getattr(config.decision_graph, "db_path", "decision_graph.db"))
        # Make db_path absolute - if relative, resolve from ai-counsel directory
        if not db_path.is_absolute():
            db_path = SERVER_DIR / db_path
        storage = DecisionGraphStorage(str(db_path))
        engine = QueryEngine(storage)

        query_text = arguments.get("query_text")
        find_contradictions = arguments.get("find_contradictions", False)
        decision_id = arguments.get("decision_id")
        limit = arguments.get("limit", 5)
        format_type = arguments.get("format", "summary")

        result = None

        if query_text:
            # Search similar decisions
            results = await engine.search_similar(query_text, limit=limit)
            result = {
                "type": "similar_decisions",
                "count": len(results),
                "results": [
                    {
                        "id": r.decision.id,
                        "question": r.decision.question,
                        "consensus": r.decision.consensus,
                        "score": r.score,
                        "participants": r.decision.participants,
                    }
                    for r in results
                ],
            }

        elif find_contradictions:
            # Find contradictions
            contradictions = await engine.find_contradictions()
            result = {
                "type": "contradictions",
                "count": len(contradictions),
                "results": [
                    {
                        "decision_id_1": c.decision_id_1,
                        "decision_id_2": c.decision_id_2,
                        "question_1": c.question_1,
                        "question_2": c.question_2,
                        "severity": c.severity,
                        "description": c.description,
                    }
                    for c in contradictions
                ],
            }

        elif decision_id:
            # Trace evolution
            timeline = await engine.trace_evolution(decision_id, include_related=True)
            result = {
                "type": "evolution",
                "decision_id": timeline.decision_id,
                "question": timeline.question,
                "consensus": timeline.consensus,
                "status": timeline.status,
                "participants": timeline.participants,
                "rounds": len(timeline.rounds),
                "related_decisions": timeline.related_decisions[:3],
            }

        if not result:
            result = {
                "error": "No query parameters provided",
                "status": "failed",
            }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in query_decisions: {type(e).__name__}: {e}", exc_info=True)
        error_response = {
            "error": str(e),
            "error_type": type(e).__name__,
            "status": "failed",
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]


async def handle_analyze_decisions(arguments: dict) -> list[TextContent]:
    """Handle analyze_decisions tool call."""
    try:
        db_path = Path(getattr(config.decision_graph, "db_path", "decision_graph.db"))
        # Make db_path absolute - if relative, resolve from ai-counsel directory
        if not db_path.is_absolute():
            db_path = SERVER_DIR / db_path
        storage = DecisionGraphStorage(str(db_path))
        engine = QueryEngine(storage)

        participant = arguments.get("participant")

        analysis = await engine.analyze_patterns(participant=participant)

        result = {
            "type": "analysis",
            "total_decisions": analysis.total_decisions,
            "total_participants": analysis.total_participants,
            "voting_patterns": [
                {
                    "participant": p.participant,
                    "total_votes": p.total_votes,
                    "avg_confidence": p.avg_confidence,
                    "preferred_options": p.preferred_options,
                }
                for p in analysis.voting_patterns
            ],
            "convergence_stats": analysis.convergence_stats,
            "participation_metrics": analysis.participation_metrics,
        }

        return [TextContent(type="text", text=json.dumps(result, indent=2))]

    except Exception as e:
        logger.error(f"Error in analyze_decisions: {type(e).__name__}: {e}", exc_info=True)
        error_response = {
            "error": str(e),
            "error_type": type(e).__name__,
            "status": "failed",
        }
        return [TextContent(type="text", text=json.dumps(error_response, indent=2))]


async def main():
    """Run the MCP server."""
    logger.info("Starting AI Counsel MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
