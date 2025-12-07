"""Agent implementations for ArenAI Grid."""
from __future__ import annotations

import random
from collections import deque
from typing import Dict, List, Optional, Tuple

import config
from entities import Action, GameState, Position, Unit


class Agent:
    def choose_actions(self, game_state: GameState) -> Dict[str, Action]:
        raise NotImplementedError


class RandomAgent(Agent):
    """Uniformly random valid actions for each unit."""

    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)

    def choose_actions(self, game_state: GameState) -> Dict[str, Action]:
        actions: Dict[str, Action] = {}
        carry_limit = getattr(game_state, "carry_limit", config.UNIT_CARRY_LIMIT)
        mode = getattr(game_state, "mode", "classic")
        control_points = getattr(game_state, "control_points", [])
        occupied = _occupied_positions(game_state)
        for player in game_state.players.values():
            for unit in player.units.values():
                if not unit.is_alive():
                    continue
                action_choices: List[Action] = [Action("idle")]
                # Harvest if on resource
                if game_state.resources:
                    if any(res.position == unit.position for res in game_state.resources) and unit.cargo_count() < carry_limit:
                        action_choices.append(Action("harvest"))
                cp_here = _control_point_at(unit.position, control_points)
                if mode != "classic" and cp_here:
                    action_choices.append(Action("stabilize"))
                    if cp_here.controller in (None, unit.owner):
                        action_choices.append(Action("pacify"))
                # Attack if adjacent
                for npos, delta in _adjacent_positions(unit.position, game_state, occupied):
                    target_unit = _unit_at_position(game_state, npos)
                    target_base = _base_at_position(game_state, npos)
                    if target_unit and target_unit.owner != unit.owner:
                        action_choices.append(Action("attack", delta))
                    if target_base and target_base.owner != unit.owner:
                        action_choices.append(Action("attack", delta))
                # Moves
                for npos, delta in _adjacent_positions(unit.position, game_state, occupied, include_bases=True):
                    if _is_cell_free(game_state, npos, occupied, unit.owner):
                        action_choices.append(Action("move", delta))
                actions[unit.uid] = self.random.choice(action_choices)
        return actions


class HeuristicAgent(Agent):
    """Simple rule-based agent with greedy objectives."""

    def __init__(self, seed: Optional[int] = None):
        self.random = random.Random(seed)

    def choose_actions(self, game_state: GameState) -> Dict[str, Action]:
        occupied = _occupied_positions(game_state)
        actions: Dict[str, Action] = {}
        for player in game_state.players.values():
            for unit in player.units.values():
                if not unit.is_alive():
                    continue
                action = self._decide_for_unit(unit, game_state, occupied)
                if action:
                    actions[unit.uid] = action
        return actions

    def _decide_for_unit(self, unit: Unit, game_state: GameState, occupied: Dict[Tuple[int, int], str]) -> Optional[Action]:
        my_base = game_state.players[unit.owner].base.position
        enemy_name = "Red" if unit.owner == "Blue" else "Blue"
        enemy_base = game_state.players[enemy_name].base.position
        carry_limit = getattr(game_state, "carry_limit", config.UNIT_CARRY_LIMIT)
        mode = getattr(game_state, "mode", "classic")
        control_points = getattr(game_state, "control_points", [])
        capture_threshold = _mode_param(game_state, "capture_threshold", 1)
        low_hp_threshold = 4 if mode == "classic" else 5

        # Attack adjacent threats/opportunities
        enemy_adjacent = self._adjacent_enemies(unit, game_state)
        if enemy_adjacent:
            # Prefer weakest adjacent target
            target = min(enemy_adjacent, key=lambda t: t.hp if isinstance(t, Unit) else 999)
            delta = _direction_from_to(unit.position, target.position)
            return Action("attack", delta)

        if mode != "classic" and control_points:
            cp_here = _control_point_at(unit.position, control_points)
            if cp_here:
                if cp_here.controller != unit.owner:
                    return Action("stabilize")
                if cp_here.controller == unit.owner and cp_here.stability < capture_threshold:
                    return Action("stabilize")
                if cp_here.controller == unit.owner and cp_here.peace_turns == 0 and self._enemy_within(unit, game_state, radius=1):
                    return Action("pacify")

        # Harvest if standing on resource and have space
        if any(res.position == unit.position for res in game_state.resources) and unit.cargo_count() < carry_limit:
            return Action("harvest")

        # Return to base if carrying loot
        if unit.cargo_count() > 0:
            step = self._step_toward(unit.position, my_base, game_state, occupied)
            if step:
                return Action("move", step)
            return Action("idle")

        # Retreat if low hp and enemy nearby
        if unit.hp <= low_hp_threshold and self._enemy_within(unit, game_state, radius=2):
            step = self._step_toward(unit.position, my_base, game_state, occupied)
            return Action("move", step) if step else Action("idle")

        if mode != "classic" and control_points:
            target_cp = self._target_control_point(unit, control_points, capture_threshold)
            if target_cp:
                step = self._step_toward(unit.position, target_cp.position, game_state, occupied)
                return Action("move", step) if step else Action("idle")

        # Move toward nearest resource, else enemy base
        target_res = self._nearest_resource(unit, game_state)
        goal = target_res.position if target_res else enemy_base
        step = self._step_toward(unit.position, goal, game_state, occupied)
        return Action("move", step) if step else Action("idle")

    def _nearest_resource(self, unit: Unit, game_state: GameState):
        if not game_state.resources:
            return None
        return min(game_state.resources, key=lambda r: unit.position.manhattan_distance(r.position))

    def _target_control_point(self, unit: Unit, control_points, capture_threshold: int):
        if not control_points:
            return None
        candidates = []
        for cp in control_points:
            if cp.controller == unit.owner and cp.stability >= capture_threshold:
                continue
            candidates.append(cp)
        if not candidates:
            return None
        return min(candidates, key=lambda cp: unit.position.manhattan_distance(cp.position))

    def _enemy_within(self, unit: Unit, game_state: GameState, radius: int) -> bool:
        for player in game_state.players.values():
            if player.name == unit.owner:
                continue
            for enemy in player.units.values():
                if enemy.is_alive() and unit.position.manhattan_distance(enemy.position) <= radius:
                    return True
        return False

    def _adjacent_enemies(self, unit: Unit, game_state: GameState):
        enemies = []
        for npos, _ in _adjacent_positions(unit.position, game_state, _occupied_positions(game_state), include_bases=True):
            enemy_unit = _unit_at_position(game_state, npos)
            enemy_base = _base_at_position(game_state, npos)
            if enemy_unit and enemy_unit.owner != unit.owner:
                enemies.append(enemy_unit)
            if enemy_base and enemy_base.owner != unit.owner:
                enemies.append(enemy_base)
        return enemies

    def _step_toward(
        self, start: Position, goal: Position, game_state: GameState, occupied: Dict[Tuple[int, int], str]
    ) -> Optional[Tuple[int, int]]:
        if start == goal:
            return None
        path = _bfs_path(start, goal, game_state, occupied)
        if len(path) >= 2:
            return _direction_from_to(path[0], path[1])
        return None


def _occupied_positions(game_state: GameState) -> Dict[Tuple[int, int], str]:
    occ: Dict[Tuple[int, int], str] = {}
    for player in game_state.players.values():
        for unit in player.units.values():
            if unit.is_alive():
                occ[(unit.position.x, unit.position.y)] = unit.owner
    return occ


def _is_cell_free(game_state: GameState, pos: Position, occupied: Dict[Tuple[int, int], str], owner: str) -> bool:
    if not (0 <= pos.x < game_state.width and 0 <= pos.y < game_state.height):
        return False
    if pos in game_state.obstacles:
        return False
    if (pos.x, pos.y) in occupied:
        return False
    for player in game_state.players.values():
        if player.base.position == pos and player.name != owner:
            return False
    return True


def _control_point_at(pos: Position, control_points):
    for cp in control_points:
        if cp.position == pos:
            return cp
    return None


def _mode_param(game_state: GameState, key: str, default: int) -> int:
    params = getattr(game_state, "mode_params", {}) or {}
    return params.get(key, default)


def _adjacent_positions(
    pos: Position, game_state: GameState, occupied: Dict[Tuple[int, int], str], include_bases: bool = False
):
    deltas = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    for dx, dy in deltas:
        np = Position(pos.x + dx, pos.y + dy)
        if not (0 <= np.x < game_state.width and 0 <= np.y < game_state.height):
            continue
        if np in game_state.obstacles:
            continue
        if not include_bases and any(player.base.position == np for player in game_state.players.values()):
            continue
        yield np, (dx, dy)


def _direction_from_to(src: Position, dst: Position) -> Tuple[int, int]:
    dx = dst.x - src.x
    dy = dst.y - src.y
    return (0 if dx == 0 else (1 if dx > 0 else -1), 0 if dy == 0 else (1 if dy > 0 else -1))


def _bfs_path(
    start: Position, goal: Position, game_state: GameState, occupied: Dict[Tuple[int, int], str]
) -> List[Position]:
    queue = deque()
    queue.append(start)
    parents: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {(start.x, start.y): None}

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for npos, _ in _adjacent_positions(current, game_state, occupied, include_bases=True):
            key = (npos.x, npos.y)
            if key in parents:
                continue
            if npos in game_state.obstacles:
                continue
            # Allow stepping on goal even if occupied by base
            if (npos.x, npos.y) in occupied and npos != goal:
                continue
            parents[key] = (current.x, current.y)
            queue.append(npos)

    if (goal.x, goal.y) not in parents:
        return [start]
    # Reconstruct path
    path = [goal]
    cur = (goal.x, goal.y)
    while parents[cur] is not None:
        cur = parents[cur]
        path.append(Position(cur[0], cur[1]))
    path.reverse()
    return path


def _unit_at_position(game_state: GameState, pos: Position) -> Optional[Unit]:
    for player in game_state.players.values():
        for unit in player.units.values():
            if unit.is_alive() and unit.position == pos:
                return unit
    return None


def _base_at_position(game_state: GameState, pos: Position):
    for player in game_state.players.values():
        if player.base.position == pos and player.base.hp > 0:
            return player.base
    return None
