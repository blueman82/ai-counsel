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
from models.schema import DeliberateRequest, DeliberationResult
from adapters import create_adapter
from deliberation.engine import DeliberationEngine

# Get the absolute path to the server directory
SERVER_DIR = Path(__file__).parent.absolute()

# Configure logging to file to avoid stdio interference
log_file = SERVER_DIR / "mcp_server.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stderr)  # Explicitly use stderr
    ]
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


# Create adapters
adapters = {}
for cli_name, cli_config in config.cli_tools.items():
    try:
        adapters[cli_name] = create_adapter(cli_name, cli_config)
        logger.info(f"Initialized adapter: {cli_name}")
    except Exception as e:
        logger.error(f"Failed to create adapter for {cli_name}: {e}")


# Create engine
engine = DeliberationEngine(adapters=adapters)


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="deliberate",
            description=(
                "Initiate true deliberative consensus where AI models debate and "
                "refine positions across multiple rounds. Models see each other's "
                "responses and can adjust their reasoning. Use for critical decisions, "
                "architecture choices, or complex technical debates."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "question": {
                        "type": "string",
                        "description": "The question or proposal for the models to deliberate on",
                        "minLength": 10
                    },
                    "participants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "cli": {
                                    "type": "string",
                                    "enum": ["claude", "codex"],
                                    "description": "CLI tool to use"
                                },
                                "model": {
                                    "type": "string",
                                    "description": "Model identifier (e.g., 'claude-3-5-sonnet-20241022', 'gpt-4')"
                                },
                                "stance": {
                                    "type": "string",
                                    "enum": ["neutral", "for", "against"],
                                    "default": "neutral",
                                    "description": "Stance for this participant"
                                }
                            },
                            "required": ["cli", "model"]
                        },
                        "minItems": 2,
                        "description": "List of AI participants (minimum 2)"
                    },
                    "rounds": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 2,
                        "description": "Number of deliberation rounds (1-5)"
                    },
                    "mode": {
                        "type": "string",
                        "enum": ["quick", "conference"],
                        "default": "quick",
                        "description": "quick = single round opinions, conference = multi-round deliberation"
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional additional context (code snippets, requirements, etc.)"
                    }
                },
                "required": ["question", "participants"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name != "deliberate":
        raise ValueError(f"Unknown tool: {name}")

    try:
        # Validate and parse request
        request = DeliberateRequest(**arguments)
        logger.info(f"Starting deliberation: {request.question[:50]}...")

        # Execute deliberation
        result = await engine.execute(request)
        logger.info(f"Deliberation complete: {result.rounds_completed} rounds")

        # Return result as JSON
        return [TextContent(
            type="text",
            text=json.dumps(result.model_dump(), indent=2)
        )]

    except Exception as e:
        logger.error(f"Error in deliberation: {e}", exc_info=True)
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "status": "failed"
            })
        )]


async def main():
    """Run the MCP server."""
    logger.info("Starting AI Counsel MCP Server...")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
