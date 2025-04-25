"""Implements the Reserve Turn Order action."""

import logging

from ..engine_utils import (
    gain_coins,
)
from ..exceptions import InvalidActionError
from ..game_state import GameState

logger = logging.getLogger(__name__)


def perform_reserve_turn_order(
    game_state: GameState, player_index: int, worker_id: int
) -> GameState:
    """Performs the Reserve Turn Order action.

    Places the specified worker on the reserve turn order location,
    pays any placement penalty, and grants the player 3 coins (for 2P).

    Args:
        game_state: The current game state.
        player_index: The index of the player performing the action.
        worker_id: The ID of the worker being placed.

    Returns:
        The potentially modified game state.

    Raises:
        InvalidActionError: If the action is invalid (wrong turn, worker unavailable,
                          insufficient coins for penalty).
    """
    # --- Input Validation ---
    if game_state.current_player_index != player_index:
        raise InvalidActionError("Not the current player's turn.")

    player_state = game_state.players[player_index]

    # Find the worker
    worker = next((w for w in player_state.workers if w.worker_id == worker_id), None)
    if worker is None:
        raise InvalidActionError(
            f"Worker ID {worker_id} not found for player {player_index}."
        )
    if worker.is_placed:
        raise InvalidActionError(f"Worker {worker_id} has already been placed.")

    location_id = "RESERVE_TURN_ORDER"

    # --- Calculate and Pay Penalty (REMOVED - Not applicable here) ---
    # penalty = calculate_placement_penalty(game_state, location_id, player_index)
    # if not can_afford(player_state, penalty):
    #     raise InsufficientResourcesError(
    #         f"Player {player_index} cannot afford penalty {penalty}"
    #     )

    # --- Apply State Changes ---
    # Note: Directly modifying state for now, prefer returning new state if possible.

    # Spend penalty (REMOVED)
    # if penalty > 0:
    #     spend_coins(player_state, penalty)
    #     logger.info(f"Player {player_index} spent {penalty} coin penalty.")

    # Place worker on board
    game_state.main_board_workers.setdefault(location_id, []).append(
        (player_index, worker_id)
    )
    # Mark worker as placed in player state
    worker.is_placed = True

    # --- Action Effect (Rule p17 - 2P) ---
    gain_coins(player_state, 3)
    logger.info(
        f"P{player_index} placed W{worker_id} on {location_id}, gained 3 coins."
        # Removed penalty info from log
    )

    # Return the modified state
    return game_state
