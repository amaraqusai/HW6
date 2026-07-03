import json
import random
import os
import asyncio
from contextlib import asynccontextmanager, AsyncExitStack
from dotenv import load_dotenv
from game import GameEngine, Config
from report_sender import ReportSender
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

# Load environment variables
load_dotenv()

class Orchestrator:
    def __init__(self):
        self.config = Config("config.json")
        self.totals = {"Cop": 0, "Thief": 0}
        self.sub_games = []
        self.cop_session = None
        self.thief_session = None
        self.file_lock = asyncio.Lock()

    def get_partial_observation(self, role, game, trajectory=None):
        # Calculate maximum coordinate distance (Chebyshev distance / radius)
        dx = abs(game.cop_pos[0] - game.thief_pos[0])
        dy = abs(game.cop_pos[1] - game.thief_pos[1])
        distance = max(dx, dy)
        
        obs = {
            "my_pos": game.cop_pos if role == "Cop" else game.thief_pos,
            "barriers": list(game.barriers),
            "moves_taken": game.moves_taken,
            "max_moves": self.config.max_moves,
            "cop_barriers_placed": game.cop_barriers_placed,
            "max_barriers": self.config.max_barriers,
            "opponent_message": getattr(game, 'last_message', 'No message yet.')
        }
        
        # Partial observability: radius 2
        if distance <= 2:
            obs["opponent_pos"] = game.thief_pos if role == "Cop" else game.cop_pos
        else:
            obs["opponent_pos"] = "unknown (out of radius)"
        
        # Include last 5 moves as history for strategic context
        if trajectory:
            recent = trajectory[-5:]
            obs["move_history"] = [
                {
                    "turn": t["turn"],
                    "action": t["action"].get("action", "move"),
                    "pos": t["action"].get("pos", []),
                    "message": t["action"].get("message", "")
                }
                for t in recent
            ]
            
        return obs

    @asynccontextmanager
    async def connect_to_server(self, server_url=None, server_script=None):
        if server_url and server_url.strip() != "":
            print(f"Connecting to remote SSE server: {server_url}")
            async with sse_client(server_url) as streams:
                async with ClientSession(*streams) as session:
                    await session.initialize()
                    yield session
        else:
            print(f"Starting local stdio server: {server_script}")
            # Ensure Python output is unbuffered
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            server_params = StdioServerParameters(command="python", args=[server_script], env=env)
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    yield session

    async def call_mcp_tool(self, turn, obs, config_dict):
        session = self.cop_session if turn == "Cop" else self.thief_session
        tool_name = "decide_cop_move" if turn == "Cop" else "decide_thief_move"
        
        for attempt in range(4):
            try:
                result = await session.call_tool(tool_name, arguments={
                    "observation_json": json.dumps(obs),
                    "config_json": json.dumps(config_dict)
                })
                content = json.loads(result.content[0].text)
                if content.get("action") == "error":
                    raise Exception(content.get("message"))
                return content
            except Exception as e:
                error_str = str(e)
                print(f"[{turn}] API/JSON Error on attempt {attempt+1}: {e}")
                if attempt == 3:
                    return {"action": "error", "message": error_str}
                # Smart backoff: if it's a rate limit, wait the suggested time
                if "RESOURCE_EXHAUSTED" in error_str:
                    wait_time = min(30, 5 * (attempt + 1))  # 5s, 10s, 15s
                    print(f"[{turn}] Rate limited. Waiting {wait_time}s before retry...")
                    await asyncio.sleep(wait_time)
                else:
                    await asyncio.sleep(2)

    async def _staggered_game(self, game_num):
        """Stagger game starts by 1.5s each to avoid simultaneous API rate limit hits."""
        await asyncio.sleep((game_num - 1) * 1.5)
        await self.play_sub_game(game_num)

    async def play_sub_game(self, game_num):
        game = GameEngine(self.config)
        turn = "Cop"
        game.last_message = "Let the game begin!"
        trajectory = []
        
        print(f"\n=== Starting Sub-Game {game_num} ===")
        while not game.winner:
            print(f"--- Turn: {turn} ---")
            obs = self.get_partial_observation(turn, game, trajectory)
            
            config_dict = {
                "grid_size": list(self.config.grid_size),
                "max_moves": self.config.max_moves,
                "max_barriers": self.config.max_barriers,
            }
            
            try:
                action = await self.call_mcp_tool(turn, obs, config_dict)
            except Exception as e:
                print(f"MCP Call Failed: {e}")
                action = {"action": "error", "message": str(e)}

            # Fallback for errors
            if action.get("action") == "error" or not action:
                print(f"LLM Error/Fallback Triggered. Reason: {action.get('message', 'Unknown')}")
                dx, dy = random.choice([(0,1), (1,0), (0,-1), (-1,0), (1,1), (-1,-1), (1,-1), (-1,1)])
                pos = game.cop_pos if turn == "Cop" else game.thief_pos
                new_pos = (pos[0] + dx, pos[1] + dy)
                action = {"action": "move", "pos": list(new_pos), "message": "Oops! Random move due to LLM error."}

            msg_to_opponent = action.get("message", "...")
            print(f"[{turn} says]: {msg_to_opponent}")
            game.last_message = msg_to_opponent
            
            trajectory.append({
                "turn": turn,
                "action": action,
                "cop_pos": list(game.cop_pos),
                "thief_pos": list(game.thief_pos),
                "barriers": list(game.barriers)
            })

            if turn == "Cop":
                if action.get("action") == "barrier":
                    success, msg = game.move_cop(place_barrier=tuple(action["pos"]))
                else:
                    success, msg = game.move_cop(new_pos=tuple(action["pos"]))
                
                if success:
                    print(f"Cop action successful: {action}")
                    turn = "Thief"
                else:
                    print(f"Cop failed action {action}: {msg}")
                    game.move_cop(new_pos=game.cop_pos) # Skip turn
                    turn = "Thief"
            else:
                success, msg = game.move_thief(new_pos=tuple(action["pos"]))
                if success:
                    print(f"Thief action successful: {action}")
                    turn = "Cop"
                else:
                    print(f"Thief failed action {action}: {msg}")
                    game.move_thief(new_pos=game.thief_pos) # Skip turn
                    turn = "Cop"
            
            # Pace the API calls to avoid Gemini free-tier rate limits (15 RPM)
            await asyncio.sleep(4)
            
            # Save partial report.json for live viewing in browser
            async with self.file_lock:
                sorted_games = sorted(self.sub_games + [{
                    "game_id": game_num,
                    "winner": None,
                    "scores": game.get_scores(),
                    "trajectory": trajectory
                }], key=lambda x: x['game_id'])
                
                partial_report = {
                    "group_name": getattr(self.config, 'group_name', 'Team-Alpha'),
                    "students": getattr(self.config, 'students', []),
                    "github_repo": "https://github.com/amaraqusai/HW6.git",
                    "sub_games": sorted_games
                }
                with open("report.json", "w") as f:
                    json.dump(partial_report, f, indent=2)
                try:
                    with open("visualizer/report.json", "w") as f:
                        json.dump(partial_report, f, indent=2)
                except:
                    pass

        print(f"Sub-Game {game_num} over! Winner: {game.winner}")
        scores = game.get_scores()
        print(f"Scores for Game {game_num}: {scores}")
        
        async with self.file_lock:
            self.totals["Cop"] += scores["Cop"]
            self.totals["Thief"] += scores["Thief"]
            self.sub_games.append({
                "game_id": game_num,
                "winner": game.winner,
                "scores": scores,
                "trajectory": trajectory
            })

    async def run_pipeline(self):
        print("Starting 6-Game Series Pipeline...")
        
        # Connect to MCP servers once and keep sessions alive
        async with AsyncExitStack() as stack:
            cop_url = getattr(self.config, 'cop_mcp_url', '')
            thief_url = getattr(self.config, 'thief_mcp_url', '')
            
            print("Initializing Cop Server connection...")
            self.cop_session = await stack.enter_async_context(self.connect_to_server(cop_url, "mcp_server_cop.py"))
            
            print("Initializing Thief Server connection...")
            self.thief_session = await stack.enter_async_context(self.connect_to_server(thief_url, "mcp_server_thief.py"))
            
            # HW specification: Role Swapping.
            # Games 1-3: Default roles. Games 4-6: Swapped AI representation.
            # Run sequentially to respect free-tier API rate limits.
            print(f"Starting {self.config.num_games} sub-games sequentially...")
            for i in range(1, self.config.num_games + 1):
                await self.play_sub_game(i)
                
        # Sort sub_games before final report
        self.sub_games.sort(key=lambda x: x['game_id'])
        print("\n=== FINAL RESULTS ===")
        print(f"Total Cop Score: {self.totals['Cop']}")
        print(f"Total Thief Score: {self.totals['Thief']}")
        
        # Build JSON Report
        report = {
            "group_name": getattr(self.config, 'group_name', 'Team-Alpha'),
            "students": getattr(self.config, 'students', []),
            "github_repo": "https://github.com/amaraqusai/HW6.git",
            "cop_mcp_url": getattr(self.config, 'cop_mcp_url', 'local_stdio') or 'local_stdio',
            "thief_mcp_url": getattr(self.config, 'thief_mcp_url', 'local_stdio') or 'local_stdio',
            "timezone": "Asia/Jerusalem",
            "sub_games": self.sub_games,
            "totals": {
                "cop": self.totals["Cop"],
                "thief": self.totals["Thief"]
            }
        }

        with open("report.json", "w") as f:
            json.dump(report, f, indent=2)
        try:
            with open("visualizer/report.json", "w") as f:
                json.dump(report, f, indent=2)
        except:
            pass
        print("\nSaved full trajectory and results to report.json")
        
        # Send via Gmail
        if os.path.exists("credentials.json"):
            print("Sending automated JSON report via Gmail API...")
            try:
                sender = ReportSender()
                sender.send_report(report)
            except Exception as e:
                print(f"Failed to send email: {e}")
        else:
            print("\nAutomated Report JSON (credentials.json missing, skipping email):")
            print(json.dumps(report, indent=2))
            
        # Plot results
        try:
            from plot_results import plot_report
            plot_report()
        except ImportError:
            pass

if __name__ == "__main__":
    orch = Orchestrator()
    asyncio.run(orch.run_pipeline())
