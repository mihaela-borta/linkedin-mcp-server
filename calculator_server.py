from mcp.server.fastmcp import FastMCP

# Create the MCP server in stdio mode
mcp = FastMCP("calculator", mode="stdio")


# Define the calculator tool
@mcp.tool()
async def calculator(operation: str, a: float, b: float) -> dict:
    """A simple calculator that can perform basic arithmetic operations."""
    result = None
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            return {"error": "Cannot divide by zero"}
        result = a / b
    else:
        return {"error": f"Unknown operation: {operation}"}

    return {"result": result}


if __name__ == "__main__":
    # Run the server
    mcp.run()
