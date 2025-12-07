"""CLI entrypoint for ArenAI Grid."""
from __future__ import annotations

import argparse
import random
import time

from agents import HeuristicAgent, RandomAgent
from game_engine import GameEngine
from game_modes import DEFAULT_MODE, GAME_MODES, get_mode
from replay import ReplayRecorder, write_js_replay
from visualizer import Visualizer


AGENT_REGISTRY = {
    "random": RandomAgent,
    "heuristic": HeuristicAgent,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run an ArenAI Grid match between two AI agents.")
    parser.add_argument("--mode", choices=GAME_MODES.keys(), default=DEFAULT_MODE, help="Game mode to run (default: world)")
    parser.add_argument("--blue", choices=AGENT_REGISTRY.keys(), default="heuristic", help="Agent for Blue")
    parser.add_argument("--red", choices=AGENT_REGISTRY.keys(), default="random", help="Agent for Red")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    parser.add_argument("--render-every", type=int, default=None, help="Render interval in turns (default depends on mode)")
    parser.add_argument("--log", action="store_true", help="Log full event list to game_log.txt")
    parser.add_argument("--no-clear", action="store_true", help="Do not clear the terminal between renders")
    parser.add_argument("--fast", action="store_true", help="Fast mode: run without per-turn rendering")
    parser.add_argument("--export-web", action="store_true", help="Export replay data for the web viewer (web/game_data.js)")
    return parser.parse_args()


def build_agent(agent_name: str, seed: int | None) -> object:
    cls = AGENT_REGISTRY[agent_name]
    # Nudge seed so both agents are not identical when using same base seed
    agent_seed = None if seed is None else seed + random.randint(0, 10000)
    return cls(seed=agent_seed)


def main() -> None:
    args = parse_args()
    seed = args.seed
    mode_def = get_mode(args.mode)
    agent_blue = build_agent(args.blue, seed)
    agent_red = build_agent(args.red, seed + 1 if seed is not None else None)
    visualizer = None if args.fast else Visualizer(
        log_to_file=args.log, clear_screen=not args.no_clear, log_file_path=mode_def.log_file
    )
    recorder = ReplayRecorder() if args.export_web else None
    interval = args.render_every if args.render_every is not None else mode_def.render_interval

    engine = GameEngine(agent_blue, agent_red, seed=seed, fast_mode=args.fast, mode_key=mode_def.key)
    start = time.time()
    winner_state = engine.play(visualizer=visualizer, render_interval=interval, recorder=recorder)
    elapsed = time.time() - start
    final_state = engine.current_state()
    blue = final_state.players["Blue"]
    red = final_state.players["Red"]

    if args.fast and args.log:
        # dump log even without rendering
        vis = Visualizer(log_to_file=True, clear_screen=False, log_file_path=mode_def.log_file)
        vis._write_events(engine.event_log)

    print("\nMatch complete.")
    print(f"Mode: {mode_def.label}")
    print(f"Winner: {winner_state.name}")
    print(f"Final score -> Blue: {blue.score} | Red: {red.score}")
    print(f"Base HP -> Blue: {blue.base.hp} | Red: {red.base.hp}")
    print(f"Units alive -> Blue: {sum(1 for u in blue.units.values() if u.is_alive())} | Red: {sum(1 for u in red.units.values() if u.is_alive())}")
    print(f"Duration: {elapsed:.2f}s")
    print(f"Seed: {seed}")
    if recorder:
        replay_dict = recorder.to_dict(winner_state.name)
        write_js_replay(replay_dict)
        print("Replay exported to web/game_data.js (open web/index.html to view).")
    if engine.event_log:
        print("Key events:")
        for line in engine.event_log[-5:]:
            print(f"- {line}")


if __name__ == "__main__":
    main()
