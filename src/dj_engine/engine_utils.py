"""Utility functions for the Darwin's Journey game engine."""

from typing import Any  # Added Any, Dict

from .constants import SealColor

# from .data_loader import MAIN_BOARD_ACTIONS_DATA # Removed direct import
from .game_state import GameState
from .player import PlayerState, WorkerState


def can_afford(player_state: PlayerState, cost: int) -> bool:
    """Checks if the player has enough coins."""
    return player_state.coins >= cost


def spend_coins(player_state: PlayerState, cost: int) -> None:
    """Subtracts coins from the player."""
    """	Assumes can_afford check passed."""
    if cost < 0:
        raise ValueError("Cost cannot be negative")
    if cost > 0:
        player_state.coins -= cost


def gain_coins(player_state: PlayerState, amount: int) -> None:
    """Adds coins to the player."""
    if amount < 0:
        raise ValueError("Amount to gain cannot be negative")
    if amount > 0:
        player_state.coins += amount


def gain_vp(player_state: PlayerState, amount: int) -> None:
    """Adds Victory Points to the player's score track."""
    # TODO: Implement logic, considering track limits?
    pass


def gain_temp_knowledge(player_state: PlayerState, amount: int) -> None:
    """Adds temporary knowledge points to the player."""
    # TODO: Implement logic
    pass


def spend_temp_knowledge(player_state: PlayerState, amount: int) -> None:
    """Subtracts temporary knowledge points. Assumes check passed."""
    # TODO: Implement logic
    pass


def check_wax_seal_req(
    worker: WorkerState,
    requirements: dict[SealColor, int],
    temp_knowledge_available: int,
) -> tuple[bool, int]:
    """Checks if a worker's seals meet requirements, using temp knowledge as wildcard.

    Returns:
        A tuple: (can_meet_requirement, temp_knowledge_spent).
    """
    temp_knowledge_needed = 0
    if not requirements:  # Handle case with no requirements
        return True, 0

    for seal_color, count_needed in requirements.items():
        count_possessed = worker.seals.get(seal_color, 0)
        deficit = count_needed - count_possessed

        if deficit > 0:
            temp_knowledge_needed += deficit

    # Check if available temporary knowledge can cover the total deficit
    if temp_knowledge_needed <= temp_knowledge_available:
        return True, temp_knowledge_needed
    else:
        return False, 0


def calculate_placement_penalty(
    game_state: GameState,
    location_id: str,
    player_index: int,
    all_game_data: dict[str, Any],
) -> int:
    """Calculates the coin penalty for placing a worker on an occupied location.
    Penalty (3 coins for 2P) only applies to CIRCULAR_MAGNIFYING_GLASS locations
    that are already occupied by one or more workers.
    """

    main_board_actions = all_game_data.get("main_board_actions", {})

    try:
        location_data = main_board_actions[location_id]
    except KeyError:
        # Location not found in main board actions data (e.g., reserve turn order)
        # No penalty applicable.
        return 0

    # No penalty for square locations or other non-applicable types
    if location_data.placement_type != "CIRCULAR_MAGNIFYING_GLASS":
        return 0

    # Check occupancy for circular locations
    occupying_placements = game_state.main_board_workers.get(location_id, [])

    if not occupying_placements:
        return 0  # Not occupied, no penalty

    # Location is circular and occupied, apply penalty (3 coins for 2P)
    # TODO: Confirm if penalty changes with player count for >2P games
    return 3
