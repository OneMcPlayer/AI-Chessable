"""Core entities and data structures for ArenAI Grid."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Position:
    x: int
    y: int

    def neighbors(self, width: int, height: int) -> List["Position"]:
        deltas = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        res = []
        for dx, dy in deltas:
            nx, ny = self.x + dx, self.y + dy
            if 0 <= nx < width and 0 <= ny < height:
                res.append(Position(nx, ny))
        return res

    def manhattan_distance(self, other: "Position") -> int:
        return abs(self.x - other.x) + abs(self.y - other.y)


@dataclass
class ResourceTile:
    rtype: str
    position: Position


@dataclass
class Base:
    owner: str  # "Blue" or "Red"
    hp: int
    position: Position


@dataclass
class Unit:
    uid: str
    owner: str
    hp: int
    attack: int
    position: Position
    carrying: Dict[str, int] = field(default_factory=dict)

    def is_alive(self) -> bool:
        return self.hp > 0

    def cargo_count(self) -> int:
        return sum(self.carrying.values())


@dataclass
class PlayerState:
    name: str
    base: Base
    units: Dict[str, Unit]  # keyed by unit id
    score: int = 0

    def living_units(self) -> List[Unit]:
        return [u for u in self.units.values() if u.is_alive()]


@dataclass
class GameState:
    """Read-only snapshot passed to agents."""

    width: int
    height: int
    obstacles: List[Position]
    resources: List[ResourceTile]
    players: Dict[str, PlayerState]
    current_turn: int
    max_turns: int

    def find_unit(self, uid: str) -> Optional[Unit]:
        for p in self.players.values():
            if uid in p.units:
                return p.units[uid]
        return None

    def copy_for_agent(self) -> "GameState":
        # Provide a shallow but safe copy; units/resources are duplicated so agents cannot mutate engine state.
        players_copy: Dict[str, PlayerState] = {}
        for name, p in self.players.items():
            units_copy = {
                uid: Unit(
                    uid=u.uid,
                    owner=u.owner,
                    hp=u.hp,
                    attack=u.attack,
                    position=u.position,
                    carrying=dict(u.carrying),
                )
                for uid, u in p.units.items()
                if u.is_alive()
            }
            players_copy[name] = PlayerState(
                name=p.name, base=Base(p.base.owner, p.base.hp, p.base.position), units=units_copy, score=p.score
            )
        resources_copy = [ResourceTile(r.rtype, r.position) for r in self.resources]
        return GameState(
            width=self.width,
            height=self.height,
            obstacles=list(self.obstacles),
            resources=resources_copy,
            players=players_copy,
            current_turn=self.current_turn,
            max_turns=self.max_turns,
        )


@dataclass
class Action:
    type: str  # "move", "harvest", "attack", "idle"
    direction: Optional[Tuple[int, int]] = None  # for move/attack

