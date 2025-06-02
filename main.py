# main.py
"""
LinkedIn MCP Server - A Model Context Protocol server for LinkedIn integration.
"""

import sys
import logging
import inquirer  # type: ignore
import atexit
from typing import Literal, NoReturn

# Import the new centralized configuration
from linkedin_mcp_server.config import get_config
from linkedin_mcp_server.cli import print_claude_config
from linkedin_mcp_server.drivers.chrome import initialize_driver
from linkedin_mcp_server.server import create_mcp_server, shutdown_handler


def setup_logging(debug: bool = False) -> None:
    """Configure logging with consistent format."""
    log_level = logging.DEBUG if debug else logging.INFO  # Changed from ERROR to INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        force=True,
        handlers=[
            logging.StreamHandler(sys.stderr)  # Ensure it goes to stderr for MCP
        ],
    )


def choose_transport_interactive() -> Literal["stdio", "sse"]:
    """Prompt user for transport mode using inquirer."""
    questions = [
        inquirer.List(
            "transport",
            message="Choose mcp transport mode",
            choices=[
                ("stdio (Default CLI mode)", "stdio"),
                ("sse (Server-Sent Events HTTP mode)", "sse"),
            ],
            default="stdio",
        )
    ]
    answers = inquirer.prompt(questions)
    return answers["transport"]


def main() -> None:
    """Initialize and run the LinkedIn MCP server."""

    # Get configuration using the new centralized system
    config = get_config()

    # Configure logging
    setup_logging(debug=False)

    logger = logging.getLogger("linkedin_mcp_server")
    logger.info("🔗 LinkedIn MCP Server 🔗")
    logger.info(f"Server configuration: {config}")

    # Add Chrome arguments from command line
    if len(sys.argv) > 1:
        for i, arg in enumerate(sys.argv):
            if arg == "--chrome-args" and i + 1 < len(sys.argv):
                config.chrome.browser_args.append(sys.argv[i + 1])
                sys.argv.pop(i)  # Remove --chrome-args
                sys.argv.pop(i)  # Remove the argument value
                break

    # Initialize the driver with configuration
    initialize_driver()

    # Decide transport
    # transport = config.server.transport
    # if config.server.setup:
    #     transport = choose_transport_interactive()

    transport = "stdio"

    # Print configuration for Claude if in setup mode
    if config.server.setup:
        print_claude_config()

    # Create and run the MCP server
    mcp = create_mcp_server()

    # Start server
    logger.info(f"\n🚀 Running LinkedIn MCP server ({transport.upper()} mode)...")
    mcp.run(transport=transport)


def exit_gracefully(exit_code: int = 0) -> NoReturn:
    """Exit the application gracefully, cleaning up resources."""
    logger = logging.getLogger("linkedin_mcp_server")
    atexit.register(lambda: logger.info("Process exiting normally"))

    if exit_code == 0:
        logger.info("👋 Shutting down LinkedIn MCP server gracefully...")
    else:
        logger.error(
            f"❌ Shutting down LinkedIn MCP server with error code {exit_code}"
        )

    try:
        logger.debug("Running shutdown handler...")
        shutdown_handler()
        logger.debug("Shutdown completed successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")
    finally:
        logger.info("LinkedIn MCP server stopped")

    sys.exit(exit_code)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        exit_gracefully(0)
    except Exception as e:
        # Setup basic logging if it wasn't already done
        if not logging.getLogger().hasHandlers():
            setup_logging(debug=False)

        logger = logging.getLogger("linkedin_mcp_server")
        logger.error(f"❌ Error running MCP server: {e}", exc_info=True)
        exit_gracefully(1)
