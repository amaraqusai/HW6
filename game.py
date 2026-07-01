import json
import random

class Config:
    def __init__(self, config_path="config.json"):
        with open(config_path, "r") as f:
            data = json.load(f)
        self.grid_size = tuple(data.get("grid_size", [5, 5]))
        self.max_moves = data.get("max_moves", 25)
        self.num_games = data.get("num_games", 6)
        self.max_barriers = data.get("max_barriers", 5)
        self.cop_mcp_url = data.get("cop_mcp_url", "")
        self.thief_mcp_url = data.get("thief_mcp_url", "")
        scoring = data.get("scoring", {})
        self.cop_win = scoring.get("cop_win", 20)
        self.thief_win = scoring.get("thief_win", 10)
        self.cop_loss = scoring.get("cop_loss", 5)
        self.thief_loss = scoring.get("thief_loss", 5)

class GameEngine:
    def __init__(self, config):
        self.config = config
        self.reset_game()

    def reset_game(self):
        self.cop_pos = self._random_pos()
        self.thief_pos = self._random_pos()
        while self.cop_pos == self.thief_pos:
            self.thief_pos = self._random_pos()
        
        self.barriers = set()
        self.cop_barriers_placed = 0
        self.moves_taken = 0
        self.winner = None

    def _random_pos(self):
        return (random.randint(0, self.config.grid_size[0] - 1),
                random.randint(0, self.config.grid_size[1] - 1))

    def is_valid_move(self, pos, new_pos):
        # Allow moving 1 step in any direction (including diagonals)
        dx = abs(new_pos[0] - pos[0])
        dy = abs(new_pos[1] - pos[1])
        
        if dx > 1 or dy > 1 or (dx == 0 and dy == 0):
            return False
            
        if not (0 <= new_pos[0] < self.config.grid_size[0] and 0 <= new_pos[1] < self.config.grid_size[1]):
            return False
            
        if new_pos in self.barriers:
            return False
            
        return True

    def move_cop(self, new_pos=None, place_barrier=None):
        if self.winner:
            return False, "Game is already over"

        if place_barrier:
            if self.cop_barriers_placed >= self.config.max_barriers:
                return False, "Max barriers reached"
            if place_barrier == self.cop_pos or place_barrier == self.thief_pos:
                 return False, "Cannot place barrier on top of an agent"
            if place_barrier in self.barriers:
                return False, "Barrier already exists here"
            if not (0 <= place_barrier[0] < self.config.grid_size[0] and 0 <= place_barrier[1] < self.config.grid_size[1]):
                return False, "Barrier out of bounds"
            
            self.barriers.add(place_barrier)
            self.cop_barriers_placed += 1
            return True, "Barrier placed"
            
        elif new_pos:
            if self.is_valid_move(self.cop_pos, new_pos):
                self.cop_pos = new_pos
                self._check_win_condition()
                return True, "Cop moved"
            return False, "Invalid move"
            
        return False, "No action provided"

    def move_thief(self, new_pos):
        if self.winner:
            return False, "Game is already over"

        if self.is_valid_move(self.thief_pos, new_pos):
            self.thief_pos = new_pos
            self.moves_taken += 1
            self._check_win_condition()
            return True, "Thief moved"
            
        return False, "Invalid move"

    def _check_win_condition(self):
        if self.cop_pos == self.thief_pos:
            self.winner = "Cop"
        elif self.moves_taken >= self.config.max_moves:
            self.winner = "Thief"

    def get_scores(self):
        if self.winner == "Cop":
            return {"Cop": self.config.cop_win, "Thief": self.config.thief_loss}
        elif self.winner == "Thief":
            return {"Cop": self.config.cop_loss, "Thief": self.config.thief_win}
        return {"Cop": 0, "Thief": 0}
