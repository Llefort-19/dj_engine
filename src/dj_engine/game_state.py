from dataclasses import dataclass, field

from .constants import GamePhase, PlayerColor, SealColor
from .data_loader import (
    BeagleGoal,
    CorrespondenceTile,
    ObjectiveTile,
    SpecialActionTile,
)
from .player import PlayerState


@dataclass
class GameState:
    """Represents the complete state of the Darwin's Journey game at any point."""

    players: list[PlayerState] = field(default_factory=list)
    current_round: int = 1
    current_phase: GamePhase = GamePhase.ROUND_ACTION
    current_player_index: int = 0
    turn_order: list[int] = field(default_factory=list)

    # --- Board State ---
    main_board_workers: dict[str, list[tuple[int, int]]] = field(
        default_factory=dict
    )  # {location_id: [(player_index, worker_id), ...]}
    available_seals: dict[SealColor, int] = field(
        default_factory=dict
    )  # {seal_color: count}
    academy_seals: list[list[SealColor | None]] = field(
        default_factory=list
    )  # List of 4 lists, each representing a scroll row
    museum_state: dict[tuple[str, int], str | None] = field(
        default_factory=dict
    )  # {(row 'A'-'D', col 1-4): token_id or None}
    museum_coins_taken: set[str] = field(default_factory=set)  # {'A', 'B', 'C', 'D'}

    # --- Specimen Tracking ---
    placed_specimens: dict[str, str | None] = field(
        default_factory=dict
    )  # {track_space_id: token_id or None}

    # --- HMS Beagle Track ---
    hms_beagle_position: str = "O0"  # Track space_id

    # --- Objectives ---
    objective_deck_silver: list[ObjectiveTile] = field(default_factory=list)
    objective_deck_gold: list[ObjectiveTile] = field(default_factory=list)
    objective_display_silver: list[ObjectiveTile] = field(default_factory=list)
    objective_display_gold: list[ObjectiveTile] = field(default_factory=list)

    # --- Correspondence ---
    correspondence_tiles_in_play: list[CorrespondenceTile] = field(default_factory=list)
    # {tile_index (0-2 relative to in_play): {player_index: stamp_count}}
    correspondence_stamps: dict[int, dict[int, int]] = field(default_factory=dict)
    used_stamps: dict[PlayerColor, int] = field(
        default_factory=dict
    )  # {player_color: count}

    # --- Beagle Goals ---
    beagle_goals_in_play: list[BeagleGoal] = field(default_factory=list)
    beagle_goals_completed: list[bool] = field(
        default_factory=list
    )  # Tracks completion status for the 5 goals in play

    # --- Special Action Tiles ---
    special_action_tiles_setup: dict[str, SpecialActionTile] = field(
        default_factory=dict
    )  # {location_id: tile}

    # --- Unlocked Locations ---
    unlocked_locations: set[str] = field(
        default_factory=set
    )  # Set of location_ids unlocked by lenses

    # --- Game Flow ---
    first_player_marker_index: int = 0
    game_over: bool = False

    # TODO: Add methods for common state lookups or manipulations if needed
