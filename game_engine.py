"""Game engine for ArenAI Grid."""
from __future__ import annotations

import os
import random
from typing import Dict, List, Optional, Tuple

import config
from entities import Action, Base, GameState, PlayerState, Position, ResourceTile, Unit


class GameEngine:
    def __init__(self, agent_blue, agent_red, seed: Optional[int] = None, fast_mode: bool = False):
        self.width = config.BOARD_WIDTH
        self.height = config.BOARD_HEIGHT
        self.max_turns = config.MAX_TURNS
        self.fast_mode = fast_mode
        self.random = random.Random(seed)

        self.obstacles: List[Position] = []
        self.resources: Dict[Tuple[int, int], ResourceTile] = {}
        self.players: Dict[str, PlayerState] = {}

        self.agents = {"Blue": agent_blue, "Red": agent_red}
        self.turn = 1
        self.event_log: List[str] = []
        self._base_destroyed: Optional[str] = None
        self._reported_dead: set[str] = set()
        self._setup_board()

    # Board setup
    def _setup_board(self) -> None:
        blue_base = Base("Blue", config.BASE_HP, Position(0, 0))
        red_base = Base("Red", config.BASE_HP, Position(self.width - 1, self.height - 1))
        self.players["Blue"] = PlayerState("Blue", base=blue_base, units=self._spawn_units("Blue", blue_base.position))
        self.players["Red"] = PlayerState("Red", base=red_base, units=self._spawn_units("Red", red_base.position))

        forbidden = {blue_base.position, red_base.position}
        self._spawn_obstacles(forbidden)
        self._spawn_resources(forbidden)

    def _spawn_units(self, owner: str, base_pos: Position) -> Dict[str, Unit]:
        units: Dict[str, Unit] = {}
        offsets = [(1, 0), (0, 1), (1, 1), (2, 0), (0, 2)]
        for i in range(config.STARTING_UNITS):
            dx, dy = offsets[i % len(offsets)]
            pos = Position(
                min(self.width - 1, base_pos.x + dx),
                min(self.height - 1, base_pos.y + dy),
            )
            uid = f"{owner[0].lower()}{i}"
            units[uid] = Unit(uid=uid, owner=owner, hp=config.UNIT_HP, attack=config.UNIT_ATTACK, position=pos)
        return units

    def _spawn_obstacles(self, forbidden: set) -> None:
        while len(self.obstacles) < config.NUM_OBSTACLES:
            pos = Position(self.random.randint(0, self.width - 1), self.random.randint(0, self.height - 1))
            if pos in forbidden:
                continue
            if pos in self.obstacles:
                continue
            self.obstacles.append(pos)
            forbidden.add(pos)

    def _spawn_resources(self, forbidden: set) -> None:
        while len(self.resources) < config.RESOURCE_SPAWN_COUNT:
            pos = Position(self.random.randint(0, self.width - 1), self.random.randint(0, self.height - 1))
            if pos in forbidden:
                continue
            if (pos.x, pos.y) in self.resources:
                continue
            rtype = self.random.choice(config.RESOURCE_TYPES)
            self.resources[(pos.x, pos.y)] = ResourceTile(rtype=rtype, position=pos)

    # Helpers
    def _position_blocked(self, pos: Position) -> bool:
        if not (0 <= pos.x < self.width and 0 <= pos.y < self.height):
            return True
        if pos in self.obstacles:
            return True
        return False

    def _unit_at(self, pos: Position) -> Optional[Unit]:
        for player in self.players.values():
            for unit in player.units.values():
                if unit.is_alive() and unit.position == pos:
                    return unit
        return None

    def _base_at(self, pos: Position) -> Optional[Base]:
        for player in self.players.values():
            if player.base.position == pos and player.base.hp > 0:
                return player.base
        return None

    def _resource_at(self, pos: Position) -> Optional[ResourceTile]:
        return self.resources.get((pos.x, pos.y))

    # Public API
    def current_state(self) -> GameState:
        return GameState(
            width=self.width,
            height=self.height,
            obstacles=list(self.obstacles),
            resources=list(self.resources.values()),
            players=self.players,
            current_turn=self.turn,
            max_turns=self.max_turns,
        ).copy_for_agent()

    def play(self, visualizer=None, render_interval: int = config.RENDER_INTERVAL, recorder=None) -> PlayerState:
        while self.turn <= self.max_turns and not self._base_destroyed:
            turn_event_start = len(self.event_log)
            for name in ("Blue", "Red"):
                if self._base_destroyed:
                    break
                self._execute_turn(name)
            if visualizer and (self.turn % render_interval == 0 or self.fast_mode):
                visualizer.render(self.current_state(), self.event_log[turn_event_start:])
            if recorder:
                recorder.record(self.current_state(), self.event_log[turn_event_start:])
            self.turn += 1
        if visualizer:
            visualizer.render(self.current_state(), self.event_log[-5:])
        if recorder:
            recorder.record(self.current_state(), self.event_log[-5:])
        return self._winner()

    def _execute_turn(self, player_name: str) -> None:
        player = self.players[player_name]
        opponent = self.players["Red" if player_name == "Blue" else "Blue"]

        # Auto deposit before deciding actions
        for unit in player.living_units():
            self._attempt_delivery(unit, player)

        state_for_agent = self.current_state()
        agent = self.agents[player_name]
        try:
            actions = agent.choose_actions(state_for_agent)
        except Exception as exc:  # Fail-safe: default to idle on agent crash
            self.event_log.append(f"Turn {self.turn}: {player_name} agent error {exc}; units idle.")
            actions = {}

        for unit in list(player.living_units()):
            action = actions.get(unit.uid) if isinstance(actions, dict) else None
            self._apply_action(unit, player, opponent, action)

        # Clean up dead units
        self._remove_dead_units(opponent, player_name)
        self._remove_dead_units(player, opponent.name)

    def _apply_action(self, unit: Unit, player: PlayerState, opponent: PlayerState, action: Optional[Action]) -> None:
        if not action:
            return
        if action.type == "move":
            self._handle_move(unit, action)
        elif action.type == "harvest":
            self._handle_harvest(unit, player)
        elif action.type == "attack":
            self._handle_attack(unit, opponent, action)
        # idle is default; no else needed

    def _handle_move(self, unit: Unit, action: Action) -> None:
        if not action.direction:
            return
        dx, dy = action.direction
        new_pos = Position(unit.position.x + dx, unit.position.y + dy)
        if self._position_blocked(new_pos):
            return
        target_base = self._base_at(new_pos)
        if self._unit_at(new_pos):
            return
        if target_base and target_base.owner != unit.owner:
            return
        unit.position = new_pos

    def _handle_harvest(self, unit: Unit, player: PlayerState) -> None:
        if unit.cargo_count() >= config.UNIT_CARRY_LIMIT:
            return
        res = self._resource_at(unit.position)
        if not res:
            return
        unit.carrying[res.rtype] = unit.carrying.get(res.rtype, 0) + 1
        del self.resources[(res.position.x, res.position.y)]
        self.event_log.append(f"Turn {self.turn}: {player.name} unit {unit.uid} harvested {res.rtype}.")

    def _handle_attack(self, unit: Unit, opponent: PlayerState, action: Action) -> None:
        if not action.direction:
            return
        dx, dy = action.direction
        target_pos = Position(unit.position.x + dx, unit.position.y + dy)
        target_unit = self._unit_at(target_pos)
        target_base = self._base_at(target_pos)
        if target_unit and target_unit.owner != unit.owner:
            target_unit.hp -= unit.attack
            if target_unit.hp <= 0:
                opponent.units[target_unit.uid].hp = 0
                self.players[unit.owner].score += config.KILL_SCORE
                self.event_log.append(
                    f"Turn {self.turn}: {unit.owner} unit {unit.uid} defeated {target_unit.owner} unit {target_unit.uid}."
                )
        elif target_base and target_base.owner != unit.owner:
            target_base.hp -= unit.attack
            self.event_log.append(
                f"Turn {self.turn}: {unit.owner} unit {unit.uid} hit {target_base.owner} base for {unit.attack}."
            )
            if target_base.hp <= 0:
                self.players[unit.owner].score += config.BASE_DESTROY_SCORE
                self._base_destroyed = target_base.owner

    def _attempt_delivery(self, unit: Unit, player: PlayerState) -> None:
        if unit.position != player.base.position:
            return
        if unit.cargo_count() == 0:
            return
        delivered_points = sum(config.RESOURCE_VALUES[r] * count for r, count in unit.carrying.items())
        if all(r in unit.carrying for r in config.RESOURCE_TYPES):
            delivered_points += config.DELIVERY_COMBO_BONUS
            combo_note = " + combo bonus"
        else:
            combo_note = ""
        player.score += delivered_points
        self.event_log.append(
            f"Turn {self.turn}: {player.name} unit {unit.uid} delivered {unit.carrying} for {delivered_points} pts{combo_note}."
        )
        unit.carrying.clear()

    def _remove_dead_units(self, player: PlayerState, killer_name: str) -> None:
        for unit in player.units.values():
            if unit.hp <= 0 and unit.uid not in self._reported_dead:
                self._reported_dead.add(unit.uid)
                self.event_log.append(f"Turn {self.turn}: {player.name} unit {unit.uid} fell in battle vs {killer_name}.")

    def _winner(self) -> PlayerState:
        blue = self.players["Blue"]
        red = self.players["Red"]
        # Endgame tie-breaker
        if self._base_destroyed == "Blue":
            return red
        if self._base_destroyed == "Red":
            return blue
        # Score comparison
        if blue.score != red.score:
            return blue if blue.score > red.score else red
        # Tie-break with remaining health
        blue_health = blue.base.hp + sum(u.hp for u in blue.living_units())
        red_health = red.base.hp + sum(u.hp for u in red.living_units())
        return blue if blue_health >= red_health else red

    # Utility to print a compact scoreline
    def scoreline(self) -> str:
        b = self.players["Blue"]
        r = self.players["Red"]
        return f"Blue {b.score} (HP {b.base.hp}) vs Red {r.score} (HP {r.base.hp})"
