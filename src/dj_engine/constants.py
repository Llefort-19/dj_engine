"""Defines constants, Enums, and possibly simple dataclasses used across the engine."""

from enum import Enum, auto


class SealColor(str, Enum):
    """Represents the colors of Wax Seals."""

    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"
    SPECIAL = "SPECIAL"  # Represents the purple special seal


class PlayerColor(str, Enum):
    """Represents the colors identifying players."""
    BLUE = "BLUE"
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class SpecimenKind(str, Enum):
    """Represents the kinds of Specimens."""

    REPTILE = "REPTILE"
    PLANT = "PLANT"
    BIRD = "BIRD"
    FOSSIL = "FOSSIL"  # Corrected from JSON


class GamePhase(Enum):
    """Represents the distinct phases of the game, aligned with round structure."""

    SETUP = auto()  # Initial game setup before rounds begin
    ROUND_ACTION = auto()
    # Players take turns placing workers and performing actions
    ROUND_TURN_ORDER = auto()  # Determine turn order for the next round
    ROUND_REWARD = auto()  # Award Beagle Goal and Correspondence rewards
    ROUND_CLEANUP = auto()  # Prepare for the next round (recall workers, etc.)
    GAME_END_SCORING = auto()  # Calculate final scores after the 5th round's cleanup
    GAME_OVER = auto()  # The game has concluded


class ActionType(Enum):
    """Represents the different types of actions possible in the game.

    Derived primarily from SimpleActionInfo.type found in JSON data.
    """

    # Core Main Board Actions
    EXPLORE = auto()
    NAVIGATE = auto()
    ACADEMY = auto()
    CORRESPONDENCE = auto()
    UNLOCK_LENS = auto()
    DELIVER_SPECIMEN = auto()
    RESEARCH_MUSEUM = auto()
    RESERVE_TURN_ORDER = auto()
    GAIN_OBJECTIVE = auto()

    # Resource Gains/Losses
    GAIN_COINS = auto()
    GAIN_VP = auto()
    GAIN_TEMP_KNOWLEDGE = auto()
    ADVANCE_THEORY = auto()

    # Objective Related
    AUTO_FULFILL_OBJECTIVE = auto()  # From Special Action Tile 1
    OBJECTIVE_REACTIVATE_TENT = auto()  # From Personal Board Objective Slot
    RESEARCH_ANY_SPECIMEN = auto()

    # Seal Related
    GAIN_SEAL_ANY_FREE = auto()  # From Campsite IA14
    GAIN_SEAL_SPECIAL = auto()  # From Special Action Tile 7

    # Movement/Placement
    PLACE_EXPLORER = auto()
    ESTABLISH_CAMPSITE = auto()
    MOVE_TO_BEAGLE = auto()
    RESEARCH_SPECIMEN = auto()  # From exploring island/ocean tiles wit specimens

    # Special actions/Crew
    CHOICE = auto()  # Represents a choice between sub-actions
    REPEAT_DELIVERY = auto()  # From Special Action Tile 3
    END_OF_ISLAND_BONUS = auto()  # From Island Track exit spaces
    COPY_CREW_CARD = auto()
    PERFORM_LOCKED_ACTION = auto()
    # TODO: Add any other action types discovered later


class TrackType(Enum):
    """Represents the different types of tracks on the board."""

    OCEAN = auto()
    ISLAND_A = auto()
    ISLAND_B = auto()
    ISLAND_C = auto()
    THEORY = auto()  # Theory of Evolution Track


class ObjectiveRequirementType(Enum):
    """Represents the types of conditions needed to fulfill objectives.

    Derived from ObjectiveRequirement.type found in objective_tiles.json.
    """

    # Types observed in JSON data
    HAVE_SEALS = auto()
    HAVE_SPECIMEN_RESEARCHED = auto()
    SHIP_AT_BEAGLE_OR_AHEAD = auto()
    HAVE_TEMP_KNOWLEDGE = auto()
    HAVE_VP = auto()
    EMPTY_STAMP_STACKS = auto()
    HAVE_LENS_TOKENS_PLACED = auto()
    HAVE_TENTS_PLACED = auto()
    HAVE_COINS = auto()
    THEORY_TRACK_AT_LEAST_AT_POSITION = auto()
    SHIP_AT_LEAST_AT_POSITION = auto()
    # Removed types not directly observed:
    # REACHED_TRACK_SPACE, HAVE_COMPLETED_OBJECTIVES,
    # HAVE_PLACED_WORKERS, HAVE_ACADEMY_TOKENS


# --- Other Game Constants ---
MAX_PLAYERS = 2  # As specified
INITIAL_STAMP_COUNT = 4 # Rule 1/2A
