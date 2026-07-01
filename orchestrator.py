import json
import random
from game import GameEngine, Config

class Orchestrator:
    def __init__(self):
        self.config = Config("config.json")
        self.game = GameEngine(self.config)
        self.turn = "Cop"

    def play_game(self):
        print("Starting Cops and Robbers game via Orchestrator...")
        while not self.game.winner:
            print(f"--- Turn: {self.turn} ---")
            if self.turn == "Cop":
                # Simulated Agent Action
                dx, dy = random.choice([(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)])
                new_pos = (self.game.cop_pos[0] + dx, self.game.cop_pos[1] + dy)
                success, msg = self.game.move_cop(new_pos=new_pos)
                if success:
                    print(f"Cop moved to {new_pos}")
                    self.turn = "Thief"
            else:
                # Simulated Agent Action
                dx, dy = random.choice([(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)])
                new_pos = (self.game.thief_pos[0] + dx, self.game.thief_pos[1] + dy)
                success, msg = self.game.move_thief(new_pos)
                if success:
                    print(f"Thief moved to {new_pos}")
                    self.turn = "Cop"

        print(f"Game over! Winner: {self.game.winner}")
        print(f"Scores: {self.game.get_scores()}")

if __name__ == "__main__":
    orch = Orchestrator()
    orch.play_game()
