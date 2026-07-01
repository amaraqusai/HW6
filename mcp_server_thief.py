from fastmcp import FastMCP

mcp = FastMCP("ThiefServer")

@mcp.tool()
def get_thief_observation(state_json: str) -> str:
    """Returns the observation for the Thief."""
    return f"Observation parsed: {state_json}"

@mcp.tool()
def send_message_to_cop(message: str) -> str:
    """Sends a natural language message to the Cop."""
    print(f"[Thief -> Cop]: {message}")
    return "Message sent."

@mcp.tool()
def verify_position(pos_x: int, pos_y: int) -> bool:
    """Mutual verification of position."""
    return True

if __name__ == "__main__":
    mcp.run()
