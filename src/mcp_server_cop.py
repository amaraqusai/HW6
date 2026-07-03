from fastmcp import FastMCP
import os
import json
from google import genai
from dotenv import load_dotenv

load_dotenv()
mcp = FastMCP("CopServer")

@mcp.tool()
def decide_cop_move(observation_json: str, config_json: str) -> str:
    """Decides the Cop's next move based on the partial observation."""
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
You are the **Cop**. Your goal is to land on the same square as the Thief to catch them.
The Thief wins if they survive for {config['max_moves']} total moves.

RULES:
- You can move 1 step in any direction (up, down, left, right, or diagonal).
- You can place up to {config['max_barriers']} barriers on empty cells to block the Thief's movement.
- You only see the Thief's position if they are within a Chebyshev radius of 2.

STRATEGY GUIDE:
- If the Thief is visible and adjacent, MOVE to their position immediately to catch them.
- If the Thief is visible but 2 cells away, consider placing a BARRIER to cut off their escape route before moving in.
- If the Thief's position is unknown, sweep the grid systematically (e.g., move toward the center or unexplored areas).
- Use barriers strategically: place them to funnel the Thief into corners or dead ends.
- You have placed {obs.get('cop_barriers_placed', 0)}/{config['max_barriers']} barriers so far.

Current Game State Observation:
{json.dumps(obs, indent=2)}
{history_text}
Provide your next move as a JSON object. First, write out your strategic reasoning in a "thought" field.
If you want to move, return: {{"thought": "your detailed strategy", "action": "move", "pos": [x, y], "message": "your trash talk to the thief"}}
If you want to place a barrier, return: {{"thought": "your detailed strategy", "action": "barrier", "pos": [x, y], "message": "your trash talk to the thief"}}
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
        print("Starting Cop Server with SSE transport on port 5000...")
        mcp.run(transport="sse", port=5000)
    else:
        mcp.run()
