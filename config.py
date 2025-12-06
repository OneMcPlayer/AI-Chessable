"""Game configuration constants for ArenAI Grid."""

# Board settings
BOARD_WIDTH = 12
BOARD_HEIGHT = 12
NUM_OBSTACLES = 14
RESOURCE_TYPES = ["R1", "R2", "R3"]
RESOURCE_VALUES = {"R1": 4, "R2": 6, "R3": 8}
RESOURCE_SPAWN_COUNT = 18
MAX_TURNS = 200

# Units and bases
STARTING_UNITS = 3
UNIT_HP = 10
UNIT_ATTACK = 3
UNIT_CARRY_LIMIT = 3
BASE_HP = 30

# Scoring
KILL_SCORE = 10
BASE_DESTROY_SCORE = 30
DELIVERY_COMBO_BONUS = 5  # Granted when delivering at least one of each resource type at once

# Visualization
RENDER_INTERVAL = 1  # Turns between renders in interactive mode
LOG_FILE = "game_log.txt"

