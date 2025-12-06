"""Terminal visualizer and logger for ArenAI Grid."""
from __future__ import annotations

import os
from typing import List, Optional

import config
from entities import GameState, Position


class Visualizer:
    def __init__(self, log_to_file: bool = False, clear_screen: bool = True):
        self.log_to_file = log_to_file
        self.clear_screen = clear_screen
        if log_to_file:
            with open(config.LOG_FILE, "w", encoding="utf-8") as f:
                f.write("ArenAI Grid match log\n")

    def render(self, state: GameState, events: List[str]) -> None:
        if self.clear_screen:
            os.system("cls" if os.name == "nt" else "clear")
        grid = [["." for _ in range(state.width)] for _ in range(state.height)]

        for obs in state.obstacles:
            grid[obs.y][obs.x] = "#"
        for res in state.resources:
            grid[res.position.y][res.position.x] = str(config.RESOURCE_TYPES.index(res.rtype) + 1)
        for player in state.players.values():
            base_char = "B" if player.name == "Blue" else "R"
            bx, by = player.base.position.x, player.base.position.y
            grid[by][bx] = base_char
            for unit in player.units.values():
                if not unit.is_alive():
                    continue
                ux, uy = unit.position.x, unit.position.y
                grid[uy][ux] = base_char.lower()

        print(f"ArenAI Grid – Turn {state.current_turn}/{state.max_turns}")
        b_state = state.players["Blue"]
        r_state = state.players["Red"]
        blue_units = sum(1 for u in b_state.units.values() if u.is_alive())
        red_units = sum(1 for u in r_state.units.values() if u.is_alive())
        print(f"Scores: Blue {b_state.score} | Red {r_state.score}")
        print(f"Units: Blue {blue_units} | Red {red_units}")
        print(f"Bases HP: Blue {b_state.base.hp} | Red {r_state.base.hp}")
        print()
        for row in grid:
            print(" ".join(row))
        print()
        if events:
            print("Recent events:")
            for line in events[-5:]:
                print(f"- {line}")
        if self.log_to_file:
            self._write_events(events)

    def _write_events(self, events: List[str]) -> None:
        with open(config.LOG_FILE, "a", encoding="utf-8") as f:
            for e in events:
                f.write(e + "\n")

    def print_final(self, winner: str, state: GameState) -> None:
        print(f"Final result: {winner} wins!")
        print(f"Scores – Blue: {state.players['Blue'].score} | Red: {state.players['Red'].score}")
