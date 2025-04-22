"""Defines the dynamic state of a player and their components (workers)."""

from dataclasses import dataclass, field

from .constants import PlayerColor, SealColor

# Assuming data_loader.py definitions are accessible
from .data_loader import ObjectiveTile


@dataclass
class WorkerState:
    """Tracks the state of a single worker belonging to a player."""

    worker_id: int
    row_index: int  # 0-4, linking to personal board row
    # Track seals placed in this specific worker's row
    seals: dict[SealColor, int] = field(default_factory=dict)
    seal_slots_filled: int = 0  # How many physical slots are covered by seals
    # ID of the crew card achieved by this worker
    assigned_crew_card_id: int | None = None


@dataclass
class PlayerState:
    """Holds the entire dynamic state for a single player."""

    player_index: int
    player_color: PlayerColor

    # --- Core Resources ---
    coins: int = 0
    temporary_knowledge: int = 0
    vp_marker_value: int = 0  # Tracks VP gained during the game (not final score total)

    # --- Components & Personal Board State ---
    workers: list[WorkerState] = field(default_factory=list)
    ship_position: str = "O0"  # Player's ship marker position (TrackSpace ID)
    evolution_marker_position: int = 0  # Player's marker on Theory track (0-36)

    explorers_available: int = 3
    # Map Island ID 'A'/'B'/'C' to current Space ID of the explorer on that island
    explorers_placed: dict[str, str] = field(default_factory=dict)

    tents_available: int = 5
    # Set of campsite_area_id where a tent has been placed
    tents_placed: set[str] = field(default_factory=set)

    # Map personal board stamp slot index (0/1/2) to remaining count
    stamps_available: dict[int, int] = field(default_factory=lambda: {0: 4, 1: 4, 2: 4})

    # Set of Specimen token_id that have been researched (token placed on grid)
    researched_specimens: set[str] = field(default_factory=set)

    # Objectives held by the player but not yet placed/fulfilled (max 2)
    objective_tiles_in_reserve: list[ObjectiveTile] = field(default_factory=list)
    # Map personal board objective slot ID ('SILVER_1', 'GOLDEN_3', etc.)
    # to the placed/achieved ObjectiveTile
    objective_slots_filled: dict[str, ObjectiveTile | None] = field(
        default_factory=dict
    )

    # Crew cards assigned during setup (IDs only)
    crew_cards_assigned_starting: list[int] = field(default_factory=list)

    lenses_available: int = 6
    # Set of BoardActionLocation.id where this player has placed a lens
    lenses_placed: set[str] = field(default_factory=set)

    # --- Game End Scoring Info ---
    # Store VP calculated during final scoring phase for specific goals
    # goal_id -> vp_scored
    beagle_goals_scored_vp: dict[int, int] = field(default_factory=dict)

    # --- Persistent Objective Effects (Flags/Modifiers) ---
    # These flags are set when the corresponding objective slot is filled
    has_free_academy_scroll_penalty_waiver: bool = False  # From Silver Objective 2
    extra_book_multiplier: int = 0  # From Silver Objective 4 (+1)
    diary_penalty_reduction: int = 0  # From Golden Objective 3 (usually 1)
    max_lag_penalty: int | None = None  # From Golden Objective 4 (usually 2)

    # Note: victory_points field removed, using vp_marker_value for tracking
    # Final VP is calculated at game end based on multiple sources.
    # Note: Seal tracking moved entirely to WorkerState.

    # TODO: Add any other player-specific state as needed
    # (e.g., first player status marker)
