"""
Basic usage example for mcp_use.

This example demonstrates how to use the mcp_use library with MCPClient
to connect any LLM to MCP tools through a unified interface.

Special thanks to https://github.com/microsoft/playwright-mcp for the server.
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from mcp_use import MCPAgent, MCPClient


async def main():
    """Run the example using a configuration file."""
    # Load environment variables
    load_dotenv()

    # Create MCPClient from config file
    client = MCPClient.from_config_file(
        os.path.join(os.path.dirname(__file__), "browser_mcp.json")
    )

    # Create LLM using LangChain's ChatAnthropic
    llm = ChatAnthropic(
        model="claude-3-sonnet-20240229",
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Create agent with the client
    agent = MCPAgent(llm=llm, client=client, max_steps=2)

    # Run the query
    result = await agent.run(
        """
        Navigate to https://groundswellag.com/speakers/molly-biddell/ and extract:
        1. The speaker's full name
        2. Details of the session they are speaking at:
           - Session title
           - Date and time
           - Location
           - Link to the session they are speaking at only if available
        Format the output in '.csv' format ';' separated:
        name;session_title;date;time;location;link
        """,
        max_steps=2,
    )
    print(f"\nResult: {result}")


if __name__ == "__main__":
    # Run the appropriate example
    asyncio.run(main())
