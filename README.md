# ArenAI Grid

A small, AI-only, turn-based grid battler where two bots gather resources, skirmish, and try to break the opposing base. The game is deliberately richer than a simple toy but compact enough to watch in the terminal.

## How to Run

```bash
python3 main.py
```

Options:
- `--blue {heuristic,random}` choose Blue agent (default: heuristic)
- `--red {heuristic,random}` choose Red agent (default: random)
- `--render-every N` render every N turns
- `--fast` run without rendering (quicker summary only)
- `--log` write the full turn-by-turn event log to `game_log.txt`
- `--seed <int>` fix randomness for repeatable matches
- `--export-web` write a replay bundle to `web/game_data.js` for browser playback

Examples:
- Heuristic vs Random with default settings: `python3 main.py`
- Random mirror match, render every 5 turns: `python3 main.py --blue random --red random --render-every 5`
- Fast headless simulation with a seed and log file: `python3 main.py --fast --seed 42 --log`
- Export a replay for the web viewer: `python3 main.py --fast --seed 7 --export-web`

## Web Viewer (Live only)
```bash
python3 serve_web.py --port 8000
```
Then visit http://localhost:8000 and click "Run Match" to generate and watch a match in the browser. The page hits `/api/run` to launch games; you can choose agents and seed in the UI.
There’s an in-page primer explaining goals, legend, and scoring so spectators can understand what’s happening.

## What You’ll See
- A 12x12 ASCII grid: obstacles `#`, bases `B/R`, units `b/r`, resources `1/2/3`.
- HUD shows turn, scores, units alive, and base HP.
- Recent events log key actions (harvests, kills, deliveries, base hits). When `--log` is used, all events are appended to `game_log.txt`.
- Final summary prints winner, scores, remaining HP, and a few highlight events.

## Rules (abridged)
- Two players: Blue and Red. Each starts with one base (30 HP) and 3 units (10 HP, 3 ATK).
- Units act once per turn (move, harvest, attack, or idle). Carry limit: 3 resources.
- Resources of three types (R1/R2/R3) spawn across the map and are worth different points. Delivering at least one of each type in a single drop grants a combo bonus.
- Points: deliver resources for value+bonus, +10 for killing a unit, +30 for destroying the enemy base.
- Game ends at 200 turns or when a base falls. Ties break via base+unit HP.

## Files
- `config.py` constants for board size, turns, unit stats, and scoring.
- `entities.py` data structures for positions, units, bases, resources, and game state snapshots.
- `agents.py` agent interface plus `RandomAgent` and `HeuristicAgent`.
- `game_engine.py` rules, validation, scoring, and turn loop.
- `visualizer.py` terminal rendering and optional logging.
- `main.py` CLI entrypoint to run matches.
- `replay.py` capture/export replays (used by the live viewer backend).
- `web/index.html` live viewer that kicks off matches via `/api/run`.
- `serve_web.py` convenience server with live API and static hosting.
- `requirements.txt` (empty, standard library only).

## Extending
- Implement new agents by subclassing `Agent` and defining `choose_actions(game_state) -> dict[uid, Action]`.
- Adjust parameters in `config.py` for quick tuning of pacing, scores, and map density.

## License
MIT License (see `LICENSE`). Contributions welcome.
