"""Implements the Academy action logic."""

import logging

from .. import engine_utils
from ..data_loader import AllGameData
from ..exceptions import GameError, InsufficientResourcesError, InvalidActionError
from ..game_state import GameState

logger = logging.getLogger(__name__)


def perform_academy_action(
    game_state: GameState,
    player_index: int,
    worker_id: int,
    location_id: str,
    chosen_scroll_row: int,  # 1-indexed row on the academy board
    chosen_seal_index: int,  # 0-indexed column within the chosen row
    use_temp_knowledge: bool,
    all_game_data: AllGameData,
) -> GameState:
    """Performs the Academy action: place worker, take wax seal, pay costs.

    Args:
        game_state: The current game state.
        player_index: Index of the player performing the action.
        worker_id: ID of the worker being placed.
        location_id: ID of the Academy action location.
        chosen_scroll_row: 1-based index of the row (scroll) chosen.
        chosen_seal_index: 0-based index of the seal within the chosen row.
        use_temp_knowledge: Flag indicating if temporary knowledge can be used.
        all_game_data: All loaded static game data.

    Returns:
        The updated game state.

    Raises:
        InvalidActionError: If the action is invalid for any reason.
        InsufficientResourcesError: If the player cannot afford the costs.
    """
    logger.info(
        f"Player {player_index} attempting Academy action at {location_id} "
        f"with worker {worker_id}, choosing seal at row {chosen_scroll_row}, "
        f"index {chosen_seal_index}."
    )

    # 1. Validate Inputs
    if game_state.current_player_index != player_index:
        raise InvalidActionError(f"It is not Player {player_index}'s turn.")

    player_state = game_state.players[player_index]
    worker = next((w for w in player_state.workers if w.worker_id == worker_id), None)
    if not worker:
        raise InvalidActionError(
            f"Worker {worker_id} not found for Player {player_index}."
        )
    if worker.is_placed:
        raise InvalidActionError(f"Worker {worker_id} has already been placed.")

    try:
        location_data = all_game_data.main_board_actions[location_id]
    except KeyError:
        raise InvalidActionError(f"Invalid location ID: {location_id}")

    # Correctly checking the string value loaded from JSON
    if location_data.action_type != "ACADEMY":
        raise InvalidActionError(
            f"Location {location_id} is not an Academy action location."
        )

    if not (1 <= chosen_scroll_row <= 4):
        raise InvalidActionError(
            f"Invalid scroll row: {chosen_scroll_row}. Must be between 1 and 4."
        )
    if not (0 <= chosen_seal_index <= 2):
        raise InvalidActionError(
            f"Invalid seal index: {chosen_seal_index}. Must be between 0 and 2."
        )

    try:
        # Ensure this access fits on one line
        row_idx = chosen_scroll_row - 1
        col_idx = chosen_seal_index
        seal_to_take = game_state.academy_seals[row_idx][col_idx]
    except IndexError:
        # This shouldn't happen with the above checks, but belts and suspenders
        raise InvalidActionError(
            f"Internal Error: Invalid academy seal coordinates ({row_idx}, {col_idx})."
        )

    if seal_to_take is None:
        raise InvalidActionError(
            f"No seal available at row {chosen_scroll_row}, index {chosen_seal_index}."
        )

    logger.debug(f"Seal to take: {seal_to_take.name}")

    # 2. Check Wax Seals Requirement
    temp_knowledge_spent = 0
    if location_data.wax_seal_requirements:
        can_meet, temp_knowledge_needed = engine_utils.check_wax_seal_req(
            worker,
            location_data.wax_seal_requirements,
            player_state.temporary_knowledge,
        )
        if not can_meet:
            raise InvalidActionError(
                f"Worker {worker_id} does not meet requirements "
                f"({location_data.wax_seal_requirements}). Needs "
                f"{temp_knowledge_needed} temp knowledge, has "
                f"{player_state.temporary_knowledge}."
            )
        if temp_knowledge_needed > 0:
            if not use_temp_knowledge:
                raise InvalidActionError(
                    f"Temp knowledge ({temp_knowledge_needed}) needed, but "
                    f"'use_temp_knowledge' is False."
                )
            temp_knowledge_spent = temp_knowledge_needed
            logger.debug(
                f"Will spend {temp_knowledge_spent} temp knowledge for seal reqs."
            )
        else:
            logger.debug("Worker meets seal requirements directly.")
    else:
        logger.debug("No wax seal requirements for this location.")

    # 3. Calculate Penalties/Costs
    # 3a. Placement Penalty
    board_actions_data = {"main_board_actions": all_game_data.main_board_actions}
    placement_penalty = engine_utils.calculate_placement_penalty(
        game_state, location_id, player_index, board_actions_data
    )
    logger.debug(f"Placement penalty: {placement_penalty} coins.")

    # 3b. Scroll Cost
    try:
        scroll_data = all_game_data.academy_scrolls[chosen_scroll_row]
    except KeyError:
        raise GameError(
            f"Internal Error: Could not find scroll data for row {chosen_scroll_row}."
        )  # Should not happen
    scroll_cost = scroll_data.cost
    logger.debug(f"Scroll cost (row {chosen_scroll_row}): {scroll_cost} coins.")

    # 3c. Personal Board Seal Placement Cost
    if not all_game_data.personal_board:
        raise GameError("Internal Error: Personal board definition not loaded.")
    personal_board_def = all_game_data.personal_board

    worker_row_def = next(
        (
            row
            for row in personal_board_def.worker_rows
            if row.row_index == worker.row_index
        ),
        None,
    )
    if not worker_row_def:
        raise GameError(f"Internal Error: No board def for row {worker.row_index}.")

    if worker.seal_slots_filled >= worker_row_def.max_seals:
        raise InvalidActionError(
            f"Worker {worker_id} cannot hold more seals (has "
            f"{worker.seal_slots_filled}/{worker_row_def.max_seals})."
        )

    try:
        # seal_slots_filled is 0-idx count of filled slots -> next empty slot idx
        seal_slot_def = worker_row_def.seal_slots[worker.seal_slots_filled]
        personal_board_cost = seal_slot_def.placement_cost
        logger.debug(
            f"Board cost (slot {worker.seal_slots_filled}): {personal_board_cost}."
        )
    except IndexError:
        # Redundant due to >= max_seals check, but safe.
        raise InvalidActionError(
            f"Worker {worker_id} cannot hold more seals (tried slot "
            f"{worker.seal_slots_filled}, max is {worker_row_def.max_seals})."
        )

    # 3d. Total Cost
    # TODO: Apply discounts (Distinctions, Objectives, etc.)
    total_cost = placement_penalty + scroll_cost + personal_board_cost
    logger.info(
        f"Total cost: {total_cost} coins (Place: {placement_penalty}, "
        f"Scroll: {scroll_cost}, Board: {personal_board_cost}). Needs "
        f"{temp_knowledge_spent} temp knowledge."
    )

    # 4. Check Affordability
    if not engine_utils.can_afford(player_state, total_cost):
        raise InsufficientResourcesError(
            f"Player {player_index} cannot afford cost {total_cost} coins "
            f"(has {player_state.coins})."
        )
    if player_state.temporary_knowledge < temp_knowledge_spent:
        raise InsufficientResourcesError(
            f"Player {player_index} needs {temp_knowledge_spent} temp knowledge, "
            f"has {player_state.temporary_knowledge}."
        )

    # 5. Apply State Changes (Mutating state from here)
    logger.info("Applying state changes for Academy action.")

    # 5a. Spend Costs
    if temp_knowledge_spent > 0:
        engine_utils.spend_temp_knowledge(player_state, temp_knowledge_spent)
        logger.info(f"Spent {temp_knowledge_spent} temporary knowledge.")
    engine_utils.spend_coins(player_state, total_cost)
    logger.info(f"Spent {total_cost} coins.")

    # 5b. Place Worker
    game_state.main_board_workers.setdefault(location_id, []).append(
        (player_index, worker_id)
    )
    worker.is_placed = True
    logger.info(f"Placed worker {worker_id} at {location_id}.")

    # 5c. Add Seal to Worker
    worker.seals[seal_to_take] = worker.seals.get(seal_to_take, 0) + 1
    worker.seal_slots_filled += 1
    logger.info(
        f"Added {seal_to_take.name} seal to worker {worker_id} "
        f"(now has {worker.seal_slots_filled} slots filled). Seals: {worker.seals}"
    )

    # 5d. Remove Seal from Academy Board
    game_state.academy_seals[row_idx][col_idx] = None
    logger.info(
        f"Removed seal from Academy row {chosen_scroll_row}, index {chosen_seal_index}."
    )

    # TODO: Apply Distinction bonuses? (e.g., Coin Refund)
    # TODO: Check for completing scroll row for bonus seal?

    # 6. Return State
    logger.info(f"Academy action completed successfully for Player {player_index}.")
    return game_state
