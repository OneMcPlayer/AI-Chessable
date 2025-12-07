# ArenAI Grid

A small, AI-only, turn-based grid battler where two bots gather resources, skirmish, and try to break the opposing base. The game now defaults to a world-scale Conquest/Peace mode (fight over cities or pacify them), with the original table-style resource race archived under a legacy mode switch.

## How to Run

```bash
python3 main.py
```

Options:
- `--mode {world,classic}` choose the ruleset (default: world conquest/peace; `classic` keeps the archived table game)
- `--blue {heuristic,random}` choose Blue agent (default: heuristic)
- `--red {heuristic,random}` choose Red agent (default: random)
- `--render-every N` render every N turns (mode defaults are applied when omitted)
- `--fast` run without rendering (quicker summary only)
- `--log` write the full turn-by-turn event log to `game_log.txt`
- `--seed <int>` fix randomness for repeatable matches
- `--export-web` write a replay bundle to `web/game_data.js` for browser playback

Examples:
- World mode, Heuristic vs Random with default settings: `python3 main.py`
- Random mirror match, render every 5 turns: `python3 main.py --blue random --red random --render-every 5`
- Legacy table game: `python3 main.py --mode classic`
- Fast headless simulation with a seed and log file: `python3 main.py --fast --seed 42 --log`
- Export a replay for the web viewer: `python3 main.py --fast --seed 7 --export-web`

## Web Viewer (Live only)
```bash
python3 serve_web.py --port 8000
```
Then visit http://localhost:8000 and click "Run Match" to generate and watch a match in the browser. The page hits `/api/run` to launch games; you can choose agents and seed in the UI.
There’s an in-page primer explaining goals, legend, and scoring so spectators can understand what’s happening.

## Modes
- **World Conquest/Peace (default):** 14x10 map with cities to stabilize for recurring influence (+3/turn) or pacify for shared peace income (+1/side/turn). Supply caches (Intel/Supplies/Aid) still deliver points and bases can be destroyed.
- **Legacy Grid (archived):** Original 12x12 resource-harvest skirmish with straightforward delivery + combat. Pick it via `--mode classic` or the web dropdown.

## What You’ll See
- A grid sized per mode: obstacles `#`, bases `B/R`, units `b/r`, resources `1/2/3`, and city sites (ring outline with a badge for controller/peace).
- HUD shows turn, scores, units alive, cities held, and base HP.
- Recent events log key actions (harvests, kills, deliveries, base hits). When `--log` is used, all events are appended to `game_log.txt`.
- Final summary prints winner, scores, remaining HP, and a few highlight events.

## Rules (abridged)
- **World Conquest/Peace:** 4 units (12 HP, 3 ATK) on each side, bases at 35 HP, up to 220 turns. Cities start neutral; stabilizing claims or fortifies them, neutralizing an enemy-held city requires working it back to neutral first. Controlled cities tick +3 score each turn; pacified cities drop control and share +1 per side for a few turns. Supply caches (Intel/Supplies/Aid) deliver for points with a combo bonus when you drop one of each.
- **Legacy Grid:** 3 units (10 HP, 3 ATK), bases at 30 HP, 200 turns. Harvest R1/R2/R3, deliver to base for points (+combo bonus), +10 per kill, +30 for destroying the enemy base.

## Files
- `config.py` constants for board size, turns, unit stats, and scoring.
- `game_modes.py` mode definitions (world default + archived classic).
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
- Adjust parameters in `config.py` or add a new entry in `game_modes.py` for quick tuning of pacing, scores, and map density.

## License
MIT License (see `LICENSE`). Contributions welcome.
