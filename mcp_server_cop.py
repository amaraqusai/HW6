from fastmcp import FastMCP

mcp = FastMCP("CopServer")

@mcp.tool()
def get_cop_observation(state_json: str) -> str:
    """Returns the observation for the Cop."""
    return f"Observation parsed: {state_json}"

@mcp.tool()
def send_message_to_thief(message: str) -> str:
    """Sends a natural language message to the Thief."""
    print(f"[Cop -> Thief]: {message}")
    return "Message sent."

@mcp.tool()
def verify_position(pos_x: int, pos_y: int) -> bool:
    """Mutual verification of position."""
    return True

if __name__ == "__main__":
    mcp.run()
