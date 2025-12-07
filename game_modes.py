"""Available game modes for ArenAI Grid."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

import config


@dataclass(frozen=True)
class ModeDefinition:
    key: str
    label: str
    description: str
    board_width: int
    board_height: int
    num_obstacles: int
    resource_types: List[str]
    resource_values: Dict[str, int]
    resource_spawn_count: int
    max_turns: int
    starting_units: int
    unit_hp: int
    unit_attack: int
    unit_carry_limit: int
    base_hp: int
    kill_score: int
    base_destroy_score: int
    delivery_combo_bonus: int
    control_points: int = 0
    capture_threshold: int = 2
    control_score: int = 3
    peace_reward: int = 1
    peace_duration: int = 4
    render_interval: int = 1
    log_file: str = "game_log.txt"

    def to_state_meta(self) -> Dict[str, object]:
        return {
            "capture_threshold": self.capture_threshold,
            "control_score": self.control_score,
            "peace_reward": self.peace_reward,
            "peace_duration": self.peace_duration,
        }


# Archived/original table-top resource skirmish
CLASSIC_MODE = ModeDefinition(
    key="classic",
    label="Legacy Grid (archived)",
    description="Original resource-harvest skirmish. Gather, deliver, and skirmish around the bases.",
    board_width=config.BOARD_WIDTH,
    board_height=config.BOARD_HEIGHT,
    num_obstacles=config.NUM_OBSTACLES,
    resource_types=config.RESOURCE_TYPES,
    resource_values=config.RESOURCE_VALUES,
    resource_spawn_count=config.RESOURCE_SPAWN_COUNT,
    max_turns=config.MAX_TURNS,
    starting_units=config.STARTING_UNITS,
    unit_hp=config.UNIT_HP,
    unit_attack=config.UNIT_ATTACK,
    unit_carry_limit=config.UNIT_CARRY_LIMIT,
    base_hp=config.BASE_HP,
    kill_score=config.KILL_SCORE,
    base_destroy_score=config.BASE_DESTROY_SCORE,
    delivery_combo_bonus=config.DELIVERY_COMBO_BONUS,
    render_interval=config.RENDER_INTERVAL,
    log_file=config.LOG_FILE,
    control_points=0,
    capture_threshold=2,
    control_score=0,
    peace_reward=0,
    peace_duration=0,
)

# New world-scale conquer/peace variant
WORLD_MODE = ModeDefinition(
    key="world",
    label="World Conquest/Peace (new)",
    description="Capture strategic cities for influence each turn or pacify them for shared peace dividends.",
    board_width=14,
    board_height=10,
    num_obstacles=18,
    resource_types=["Intel", "Supplies", "Aid"],
    resource_values={"Intel": 4, "Supplies": 6, "Aid": 8},
    resource_spawn_count=10,
    max_turns=220,
    starting_units=4,
    unit_hp=12,
    unit_attack=3,
    unit_carry_limit=3,
    base_hp=35,
    kill_score=10,
    base_destroy_score=35,
    delivery_combo_bonus=6,
    render_interval=1,
    log_file="game_log.txt",
    control_points=7,
    capture_threshold=2,
    control_score=3,
    peace_reward=1,
    peace_duration=4,
)

GAME_MODES: Dict[str, ModeDefinition] = {
    WORLD_MODE.key: WORLD_MODE,
    CLASSIC_MODE.key: CLASSIC_MODE,
}

DEFAULT_MODE = WORLD_MODE.key


def get_mode(key: str) -> ModeDefinition:
    if key not in GAME_MODES:
        raise ValueError(f"Unknown mode '{key}'. Valid modes: {list(GAME_MODES.keys())}")
    return GAME_MODES[key]
