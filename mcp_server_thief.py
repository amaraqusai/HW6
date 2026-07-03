from fastmcp import FastMCP
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
mcp = FastMCP("ThiefServer")

@mcp.tool()
def decide_thief_move(observation_json: str, config_json: str) -> str:
    """Decides the Thief's next move based on the partial observation."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return json.dumps({"action": "error", "message": "No API key"})
    
    client = genai.Client(vertexai=False, api_key=api_key)
    obs = json.loads(observation_json)
    config = json.loads(config_json)
    
    prompt = f"""
You are playing Cops and Robbers on a {config['grid_size'][0]}x{config['grid_size'][1]} grid.
You are the Thief. You want to survive for {config['max_moves']} moves.
The Cop wins if they land on your square.
Note: You only see the Cop's position if they are within a radius of 2.

Current Game State Observation:
{json.dumps(obs, indent=2)}

Provide your next move as a JSON object. First, write out your strategic reasoning in a "thought" field.
If you want to move (up to 1 step in any direction, including diagonals), return: {{"thought": "your strategy", "action": "move", "pos": [x, y], "message": "your message to opponent"}}
If you want to wait, return: {{"thought": "your strategy", "action": "move", "pos": [current_x, current_y], "message": "your message to opponent"}}
Respond ONLY with valid JSON.
"""
    try:
        response = client.models.generate_content(
            model='gemini-flash-lite-latest',
            contents=prompt,
            config=genai.types.GenerateContentConfig(response_mime_type="application/json")
        )
        return response.text
    except Exception as e:
        return json.dumps({"action": "error", "message": str(e)})

if __name__ == "__main__":
    import sys
    if "--sse" in sys.argv:
        print("Starting Thief Server with SSE transport on port 5001...")
        mcp.run(transport="sse", port=5001)
    else:
        mcp.run()
