import json
import random
import os
from dotenv import load_dotenv
from google import genai
from game import GameEngine, Config

# Load environment variables (e.g., GEMINI_API_KEY)
load_dotenv()

class Orchestrator:
    def __init__(self):
        self.config = Config("config.json")
        self.game = GameEngine(self.config)
        self.turn = "Cop"
        
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            self.client = genai.Client(api_key=api_key)
        else:
            self.client = None
            print("Warning: GEMINI_API_KEY not found. Using random moves instead.")

    def get_agent_move(self, role, observation):
        if not self.client:
            return None

        prompt = f"""
You are playing a game of Cops and Robbers on a {self.config.grid_size[0]}x{self.config.grid_size[1]} grid.
You are the {role}. 
The Cop wants to land on the same square as the Thief.
The Thief wants to survive for {self.config.max_moves} moves.
Current Game State Observation:
{json.dumps(observation, indent=2)}

Provide your next move as a JSON object:
If you want to move (up to 1 step in any direction, including diagonals), return: {{"action": "move", "pos": [x, y]}}
If you are the Cop and want to place a barrier, return: {{"action": "barrier", "pos": [x, y]}}
Respond ONLY with valid JSON.
"""
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=genai.types.GenerateContentConfig(response_mime_type="application/json")
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"LLM Error: {e}, falling back to random move")
            return None

    def get_observation(self, role):
        # Full observation for testing; in real game, this might be partial (e.g. radius)
        return {
            "my_pos": self.game.cop_pos if role == "Cop" else self.game.thief_pos,
            "opponent_pos": self.game.thief_pos if role == "Cop" else self.game.cop_pos,
            "barriers": list(self.game.barriers),
            "moves_taken": self.game.moves_taken,
            "max_moves": self.config.max_moves,
            "cop_barriers_placed": self.game.cop_barriers_placed,
            "max_barriers": self.config.max_barriers
        }

    def play_game(self):
        print("Starting Cops and Robbers game with LLM integration...")
        while not self.game.winner:
            print(f"--- Turn: {self.turn} ---")
            observation = self.get_observation(self.turn)
            action = self.get_agent_move(self.turn, observation)

            if not action:
                # Random fallback
                dx, dy = random.choice([(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)])
                pos = self.game.cop_pos if self.turn == "Cop" else self.game.thief_pos
                new_pos = (pos[0] + dx, pos[1] + dy)
                action = {"action": "move", "pos": list(new_pos)}

            if self.turn == "Cop":
                if action.get("action") == "barrier":
                    success, msg = self.game.move_cop(place_barrier=tuple(action["pos"]))
                else:
                    success, msg = self.game.move_cop(new_pos=tuple(action["pos"]))
                
                if success:
                    print(f"Cop action successful: {action}")
                    self.turn = "Thief"
                else:
                    print(f"Cop failed action {action}: {msg}")
                    # Force a valid random move to avoid infinite loop on bad LLM output
                    dx, dy = random.choice([(0,0)]) # Wait, don't move
                    self.game.move_cop(new_pos=self.game.cop_pos)
                    self.turn = "Thief"
            else:
                success, msg = self.game.move_thief(new_pos=tuple(action["pos"]))
                if success:
                    print(f"Thief action successful: {action}")
                    self.turn = "Cop"
                else:
                    print(f"Thief failed action {action}: {msg}")
                    self.game.move_thief(new_pos=self.game.thief_pos)
                    self.turn = "Cop"

        print(f"Game over! Winner: {self.game.winner}")
        print(f"Scores: {self.game.get_scores()}")

if __name__ == "__main__":
    orch = Orchestrator()
    orch.play_game()
