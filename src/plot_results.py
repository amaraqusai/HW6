import json
import matplotlib.pyplot as plt
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def plot_report(report_path=None):
    if report_path is None:
        report_path = os.path.join(BASE_DIR, "output", "report.json")
        
    if not os.path.exists(report_path):
        print(f"{report_path} not found. Run the orchestrator first.")
        return

    with open(report_path, "r") as f:
        data = json.load(f)
        
    sub_games = data.get("sub_games", [])
    if not sub_games:
        print("No sub_games found in report.json")
        return

    cop_scores = [game["scores"]["Cop"] for game in sub_games]
    thief_scores = [game["scores"]["Thief"] for game in sub_games]
    games = [f"Game {game['game_id']}" for game in sub_games]
    
    x = range(len(games))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar([i - width/2 for i in x], cop_scores, width, label='Cop Score', color='#1f77b4')
    ax.bar([i + width/2 for i in x], thief_scores, width, label='Thief Score', color='#ff7f0e')
    
    ax.set_ylabel('Scores')
    ax.set_title('Cop vs Thief Scores per Sub-Game')
    ax.set_xticks(x)
    ax.set_xticklabels(games)
    ax.legend()
    
    plt.tight_layout()
    output_path = os.path.join(BASE_DIR, "output", "results.png")
    plt.savefig(output_path, dpi=300)
    print(f"Generated {output_path} successfully.")

if __name__ == "__main__":
    plot_report()
