"""Replay recording and export helpers for ArenAI Grid web visualization."""
from __future__ import annotations

import json
import os
from typing import Dict, List

from entities import GameState


class ReplayRecorder:
    """Captures turn-by-turn snapshots that can be rendered on the web."""

    def __init__(self):
        self.frames: List[Dict] = []
        self.meta: Dict[str, int] = {}

    def record(self, state: GameState, events: List[str]) -> None:
        if not self.meta:
            self.meta = {"width": state.width, "height": state.height, "maxTurns": state.max_turns}
        frame = {
            "turn": state.current_turn,
            "events": list(events),
            "obstacles": [[p.x, p.y] for p in state.obstacles],
            "resources": [{"t": r.rtype, "p": [r.position.x, r.position.y]} for r in state.resources],
            "bases": {
                name: {"hp": p.base.hp, "pos": [p.base.position.x, p.base.position.y], "score": p.score}
                for name, p in state.players.items()
            },
            "units": {
                name: [
                    {
                        "id": u.uid,
                        "hp": u.hp,
                        "pos": [u.position.x, u.position.y],
                        "cargo": u.carrying,
                    }
                    for u in p.units.values()
                    if u.is_alive()
                ]
                for name, p in state.players.items()
            },
        }
        self.frames.append(frame)

    def to_dict(self, winner: str | None = None) -> Dict:
        data = {"meta": self.meta, "frames": self.frames}
        if winner:
            data["winner"] = winner
        return data


def write_js_replay(replay: Dict, path: str = "web/game_data.js") -> None:
    """Write replay data to a JS file that defines `const replayData = ...`."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("const replayData = ")
        json.dump(replay, f)
        f.write(";\n")

