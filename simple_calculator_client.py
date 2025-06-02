import asyncio
from mcp_use import MCPClient


async def main():
    # Create configuration for the calculator server in stdio mode
    config = {
        "mcpServers": {
            "calculator": {"command": "uv", "args": ["run", "calculator_server.py"]}
        }
    }

    # Create MCPClient from configuration
    client = MCPClient.from_dict(config)

    try:
        # Create a session to connect to the calculator server
        session = await client.create_session("calculator")

        # Example calculations
        calculations = [
            {"operation": "add", "a": 5, "b": 3},
            {"operation": "multiply", "a": 8, "b": 2},
            {"operation": "divide", "a": 16, "b": 4},
        ]

        # Process each calculation
        for calc in calculations:
            # Call the calculator tool directly
            result = await session.connector.call_tool("calculator", calc)
            print(f"Calculation: {calc}")
            print(f"Result: {result.content}\n")

    finally:
        # Clean up
        await client.close_all_sessions()


if __name__ == "__main__":
    asyncio.run(main())
