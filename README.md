# Dual AI Agent Conversation via MCP Servers

## Overview
This project implements Assignment 6: Cops and Robbers chase between autonomous agents in a partially observable environment using MCP servers.

## Dec-POMDP Formulation
The problem is modeled as a Decentralized Partially Observable Markov Decision Process (Dec-POMDP):

$\langle n, S, \{A_i\}, P, R, \{\Omega_i\}, O, \gamma \rangle$

- **$n$**: Number of agents (2: Cop and Thief)
- **$S$**: State space, representing the physical grid positions of the Cop, Thief, and the placed barriers.
- **$A_i$**: Action space for agent $i$. Includes movement (1 step any direction) and barrier placement for the Cop.
- **$P$**: State transition probability function, defining deterministic movement unless blocked by a barrier or edge of the board.
- **$R$**: Reward function (Scoring table: Cop win 20, Thief loss 5, etc).
- **$\Omega_i$**: Observation space for agent $i$, reflecting partial observability.
- **$O$**: Observation probability function.
- **$\gamma$**: Discount factor (for optional Q-Learning implementation).

## Architecture
- **MCP Protocol**: The agents' tools are exposed via `fastmcp` (MCP Server), allowing local and remote AI orchestration.
- **LLM Engine**: `google-genai` is used to allow the agents to deduce opponents' positions and exchange natural language messages.
- **Game Engine**: A custom local `GameEngine` manages the rules, sub-games, barriers, and turns.
- **Gmail API**: Integrated `report_sender.py` to automatically dispatch the JSON summary of the sub-games to the course staff.

## Installation & Setup
1. Define parameters in `config.json`
2. Create a `.env` file and set `GEMINI_API_KEY=your_api_key_here`
3. Create `credentials.json` from Google Cloud Console for the Gmail API if you wish to run `report_sender.py`.
4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game locally
```bash
python orchestrator.py
```
