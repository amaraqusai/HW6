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
    
    # Build move history context
    history_text = ""
    move_history = obs.get("move_history", [])
    if move_history:
        history_text = "\nRecent Move History (last few turns):\n"
        for entry in move_history:
            history_text += f"  - {entry['turn']}: {entry['action']} to {entry.get('pos', '?')} | said: \"{entry.get('message', '')}\"\n"
    
    prompt = f"""You are playing Cops and Robbers on a {config['grid_size'][0]}x{config['grid_size'][1]} grid.
You are the **Thief**. Your goal is to SURVIVE for {config['max_moves']} total moves without getting caught.
The Cop wins if they land on your square. You have survived {obs.get('moves_taken', 0)}/{config['max_moves']} moves so far.

RULES:
- You can move 1 step in any direction (up, down, left, right, or diagonal).
- You can also WAIT (stay in place) by moving to your current position.
- You cannot move through barriers.
- You only see the Cop's position if they are within a Chebyshev radius of 2.

STRATEGY GUIDE:
- If the Cop is visible and adjacent (1 cell away), FLEE immediately in the opposite direction.
- If the Cop is visible but 2 cells away, move to maximize distance while avoiding corners.
- If the Cop's position is unknown, stay near the CENTER of the grid to maximize escape routes.
- AVOID corners and edges — they limit your escape options.
- Watch for barriers that might trap you. Always keep at least 2 escape routes open.
- Use the move history to predict the Cop's patrol pattern and stay ahead.

Current Game State Observation:
{json.dumps(obs, indent=2)}
{history_text}
Provide your next move as a JSON object. First, write out your strategic reasoning in a "thought" field.
To move, return: {{"thought": "your detailed evasion strategy", "action": "move", "pos": [x, y], "message": "your trash talk to the cop"}}
To wait in place, return: {{"thought": "your detailed strategy", "action": "move", "pos": [{obs.get('my_pos', [0,0])[0]}, {obs.get('my_pos', [0,0])[1]}], "message": "your trash talk to the cop"}}
Respond ONLY with valid JSON.
"""
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
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
