"""Tests for the Academy action and related utility functions."""

from dataclasses import replace
from typing import Any

import pytest

from src.dj_engine.actions.academy import perform_academy_action
from src.dj_engine.constants import PlayerColor, SealColor
from src.dj_engine.data_loader import (
    AcademyScroll,
    AllGameData,
    BoardActionLocation,
    PersonalBoardDefinition,
    PersonalBoardSealSlot,
    PersonalBoardWorkerRow,  # Needed for mock definitions
)
from src.dj_engine.exceptions import (
    GameError,
    InsufficientResourcesError,
    InvalidActionError,
)
from src.dj_engine.game_state import GameState
from src.dj_engine.player import PlayerState, WorkerState

# --- Mock engine_utils functions for testing ---
# (Replace with actual imports if they exist elsewhere)


def check_wax_seal_req(
    worker: WorkerState, requirements: dict[SealColor, int], temp_knowledge: int
) -> tuple[bool, int]:
    """Mock implementation for testing."""
    needed_knowledge = 0
    for color, count in requirements.items():
        if worker.seals.get(color, 0) < count:
            needed_knowledge += count - worker.seals.get(color, 0)

    can_meet_directly = needed_knowledge == 0
    can_meet_with_knowledge = temp_knowledge >= needed_knowledge

    if can_meet_directly:
        return True, 0
    elif can_meet_with_knowledge:
        return True, needed_knowledge
    else:
        return False, needed_knowledge


def calculate_placement_penalty(
    game_state: GameState,
    location_id: str,
    player_index: int,
    static_data: dict[str, Any],
) -> int:
    """Mock implementation for testing."""
    location_data = static_data["main_board_actions"][location_id]
    occupying_workers = game_state.main_board_workers.get(location_id, [])
    other_players_workers = [
        (p_idx, w_id) for p_idx, w_id in occupying_workers if p_idx != player_index
    ]

    if not other_players_workers:
        return 0

    if location_data.placement_type == "CIRCULAR_MAGNIFYING_GLASS":
        # Penalty is 1 coin per unique other player present
        return len(set(p_idx for p_idx, w_id in other_players_workers))
    elif location_data.placement_type == "SQUARE_MAGNIFYING_GLASS":
        # Penalty is 1 coin per worker from other players present
        return len(other_players_workers)
    else:
        return 0  # Should not happen for academy


def can_afford(player_state: PlayerState, cost: int) -> bool:
    """Mock implementation for testing."""
    return player_state.coins >= cost


def spend_temp_knowledge(player_state: PlayerState, amount: int) -> None:
    """Mock implementation for testing."""
    if player_state.temporary_knowledge < amount:
        raise InsufficientResourcesError("Not enough temp knowledge")
    player_state.temporary_knowledge -= amount


def spend_coins(player_state: PlayerState, amount: int) -> None:
    """Mock implementation for testing."""
    if player_state.coins < amount:
        raise InsufficientResourcesError("Not enough coins")
    player_state.coins -= amount


# --- Pytest Fixtures ---


@pytest.fixture
def base_worker() -> WorkerState:
    return WorkerState(
        worker_id=1, row_index=1, seals={}, seal_slots_filled=0, is_placed=False
    )


@pytest.fixture
def player_state_fixture(base_worker: WorkerState) -> PlayerState:
    # Only provide arguments accepted by __init__ or fields with defaults
    # we want to override
    return PlayerState(
        player_index=0,
        player_color=PlayerColor.BLUE,
        workers=[base_worker],  # Override default_factory
        coins=10,  # Override default=0
        temporary_knowledge=2,  # Override default=0
        # REMOVE all other arguments like objectives, crew, wax_seals, etc.
        # as they are likely handled by default_factory or internal logic.
    )


@pytest.fixture
def academy_location() -> BoardActionLocation:
    return BoardActionLocation(
        id="ACADEMY_1",
        action_type="ACADEMY",
        diary_type="MAIN",
        placement_type="CIRCULAR_MAGNIFYING_GLASS",
        wax_seal_requirements={SealColor.RED: 1},
        base_actions=[],
        distinction_bonuses={},
    )


@pytest.fixture
def academy_location_square() -> BoardActionLocation:
    # Square placement type for penalty testing
    return BoardActionLocation(
        id="ACADEMY_2",
        action_type="ACADEMY",
        diary_type="MAIN",
        placement_type="SQUARE_MAGNIFYING_GLASS",
        wax_seal_requirements={},
        base_actions=[],
        distinction_bonuses={},
    )


@pytest.fixture
def academy_scroll() -> AcademyScroll:
    return AcademyScroll(id="scroll_1", scroll_row=1, cost=2, slots=3)


@pytest.fixture
def personal_board_def() -> PersonalBoardDefinition:
    return PersonalBoardDefinition(
        board_id="test_board",
        worker_rows=[
            PersonalBoardWorkerRow(
                row_index=1,
                max_seals=3,
                seal_slots=[
                    PersonalBoardSealSlot(
                        slot_index=0,
                        placement_cost=1,
                        distinction_trigger=None,
                        reward_action=None,
                    ),
                    PersonalBoardSealSlot(
                        slot_index=1,
                        placement_cost=2,
                        distinction_trigger=None,
                        reward_action=None,
                    ),
                    PersonalBoardSealSlot(
                        slot_index=2,
                        placement_cost=3,
                        distinction_trigger="SILVER",
                        reward_action=None,
                    ),
                ],
            )
        ],
        objective_slots=[],
        reserve_objective_slots=[],
        tent_slots=[],
        stamp_slots=[],
        specimen_grid_slots=[],
        objective_pair_bonus_action=None,
    )


@pytest.fixture
def all_game_data_fixture(
    academy_location: BoardActionLocation,
    academy_scroll: AcademyScroll,
    personal_board_def: PersonalBoardDefinition,
    academy_location_square: BoardActionLocation,
) -> AllGameData:
    return AllGameData(
        academy_scrolls={1: academy_scroll},
        main_board_actions={
            "ACADEMY_1": academy_location,
            "ACADEMY_2": academy_location_square,
        },
        personal_board=personal_board_def,
        # Add other necessary data with default/empty values
        beagles_goals={},
        campsites={},
        correspondences_tiles={},
        crew_cards={},
        island_a_track={},
        island_b_track={},
        island_c_track={},
        objective_display_area=None,
        objective_tiles={},
        ocean_track={},
        special_action_tiles={},
        species={},
        theory_track={},
    )


@pytest.fixture
def game_state_fixture(player_state_fixture: PlayerState) -> GameState:
    # Only provide arguments that need non-default values for the tests
    return GameState(
        players=[player_state_fixture],  # Override default_factory
        current_player_index=0,  # Override default
        academy_seals=[
            [SealColor.RED, SealColor.BLUE, SealColor.GREEN],  # Row 1
            [SealColor.YELLOW, SealColor.SPECIAL, SealColor.RED],  # Row 2
            [SealColor.BLUE, SealColor.GREEN, SealColor.YELLOW],  # Row 3
            [SealColor.SPECIAL, SealColor.RED, SealColor.BLUE],  # Row 4
        ],  # Override default_factory
        main_board_workers={},  # Override default_factory (start empty)
        # REMOVE all other arguments like round_number, current_phase, etc.
        # Let them use their defaults from the GameState definition.
    )


# --- Tests for engine_utils.check_wax_seal_req ---


@pytest.mark.parametrize(
    "worker_seals, requirements, temp_knowledge, expected_can_meet, expected_needed",
    [
        # Meets directly
        ({SealColor.RED: 1}, {SealColor.RED: 1}, 2, True, 0),
        ({SealColor.RED: 1, SealColor.BLUE: 1}, {SealColor.RED: 1}, 2, True, 0),
        ({}, {}, 2, True, 0),  # No requirements
        # Needs temp knowledge, has enough
        ({}, {SealColor.RED: 1}, 1, True, 1),
        ({}, {SealColor.RED: 1}, 2, True, 1),
        ({SealColor.RED: 1}, {SealColor.RED: 2}, 1, True, 1),
        ({SealColor.RED: 1}, {SealColor.RED: 2, SealColor.BLUE: 1}, 2, True, 2),
        # Needs temp knowledge, not enough
        ({}, {SealColor.RED: 1}, 0, False, 1),
        ({SealColor.RED: 1}, {SealColor.RED: 2}, 0, False, 1),
        ({SealColor.RED: 1}, {SealColor.RED: 2, SealColor.BLUE: 1}, 1, False, 2),
    ],
)
def test_check_wax_seal_req(
    base_worker: WorkerState,
    worker_seals: dict[SealColor, int],
    requirements: dict[SealColor, int],
    temp_knowledge: int,
    expected_can_meet: bool,
    expected_needed: int,
) -> None:
    worker = replace(base_worker, seals=worker_seals)
    can_meet, needed = check_wax_seal_req(worker, requirements, temp_knowledge)
    assert can_meet == expected_can_meet
    assert needed == expected_needed


# --- Tests for engine_utils.calculate_placement_penalty ---


@pytest.mark.parametrize(
    "location_id, workers_on_location, current_player_idx, expected_penalty",
    [
        # Unoccupied
        ("ACADEMY_1", {}, 0, 0),
        # Circular: Occupied only by current player
        ("ACADEMY_1", {"ACADEMY_1": [(0, 1)]}, 0, 0),
        # Circular: Occupied by one other player (1 worker)
        ("ACADEMY_1", {"ACADEMY_1": [(1, 2)]}, 0, 1),
        # Circular: Occupied by one other player (2 workers)
        ("ACADEMY_1", {"ACADEMY_1": [(1, 2), (1, 3)]}, 0, 1),
        # Circular: Occupied by two other players (1 worker each)
        ("ACADEMY_1", {"ACADEMY_1": [(1, 2), (2, 4)]}, 0, 2),
        # Circular: Occupied by current and other players
        ("ACADEMY_1", {"ACADEMY_1": [(0, 1), (1, 2), (2, 4)]}, 0, 2),
        # Square: Occupied only by current player
        ("ACADEMY_2", {"ACADEMY_2": [(0, 1)]}, 0, 0),
        # Square: Occupied by one other player (1 worker)
        ("ACADEMY_2", {"ACADEMY_2": [(1, 2)]}, 0, 1),
        # Square: Occupied by one other player (2 workers)
        ("ACADEMY_2", {"ACADEMY_2": [(1, 2), (1, 3)]}, 0, 2),
        # Square: Occupied by two other players (1 worker each)
        ("ACADEMY_2", {"ACADEMY_2": [(1, 2), (2, 4)]}, 0, 2),
        # Square: Occupied by two other players (mixed workers)
        ("ACADEMY_2", {"ACADEMY_2": [(1, 2), (1, 3), (2, 4)]}, 0, 3),
        # Square: Occupied by current and other players
        ("ACADEMY_2", {"ACADEMY_2": [(0, 1), (1, 2), (1, 3), (2, 4)]}, 0, 3),
    ],
)
def test_calculate_placement_penalty(
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    location_id: str,
    workers_on_location: dict[str, list[tuple[int, int]]],
    current_player_idx: int,
    expected_penalty: int,
) -> None:
    game_state = replace(
        game_state_fixture,
        main_board_workers=workers_on_location,
        current_player_index=current_player_idx,
    )
    static_data_subset = {
        "main_board_actions": all_game_data_fixture.main_board_actions
    }
    penalty = calculate_placement_penalty(
        game_state, location_id, current_player_idx, static_data_subset
    )
    assert penalty == expected_penalty


# --- Tests for perform_academy_action ---


def test_perform_academy_action_valid_no_temp_knowledge(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    """Test a successful academy action without needing temporary knowledge."""
    # Patch dependencies using mocker
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 0)
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty", return_value=0
    )
    mocker.patch("src.dj_engine.engine_utils.can_afford", return_value=True)
    # Mock the side effects directly if not asserting calls
    mocker.patch(
        "src.dj_engine.engine_utils.spend_coins", side_effect=spend_coins
    )  # Use mock helper
    mocker.patch(
        "src.dj_engine.engine_utils.spend_temp_knowledge",
        side_effect=spend_temp_knowledge,
    )

    # Setup
    initial_coins = 10
    initial_knowledge = 1
    worker = replace(base_worker, seals={SealColor.RED: 1})
    player_state = replace(
        player_state_fixture,
        workers=[worker],
        coins=initial_coins,
        temporary_knowledge=initial_knowledge,
    )
    game_state = replace(game_state_fixture, players=[player_state])
    location_id = "ACADEMY_1"
    chosen_scroll_row = 1  # Cost 2
    chosen_seal_index = 1  # BLUE Seal
    worker_id = worker.worker_id
    # personal_board_cost = 1 # Unused variable
    expected_total_cost = 0 + 2 + 1  # Placement + Scroll + Board

    updated_state = perform_academy_action(
        game_state,
        0,
        worker_id,
        location_id,
        chosen_scroll_row,
        chosen_seal_index,
        False,
        all_game_data_fixture,
    )

    # Assertions on the returned state
    final_player_state = updated_state.players[0]
    final_worker_state = final_player_state.workers[0]

    assert final_player_state.coins == initial_coins - expected_total_cost
    assert final_player_state.temporary_knowledge == initial_knowledge  # Unchanged
    assert final_worker_state.is_placed
    assert final_worker_state.seals.get(SealColor.BLUE) == 1
    assert final_worker_state.seal_slots_filled == 1
    assert updated_state.main_board_workers[location_id] == [(0, worker_id)]
    assert updated_state.academy_seals[chosen_scroll_row - 1][chosen_seal_index] is None


def test_perform_academy_action_valid_with_temp_knowledge(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    """Test a successful academy action using temporary knowledge for seal req."""
    expected_temp_knowledge_cost = 1
    # Patch dependencies using mocker
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req",
        return_value=(True, expected_temp_knowledge_cost),
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty", return_value=0
    )
    mocker.patch("src.dj_engine.engine_utils.can_afford", return_value=True)
    mocker.patch("src.dj_engine.engine_utils.spend_coins", side_effect=spend_coins)
    mocker.patch(
        "src.dj_engine.engine_utils.spend_temp_knowledge",
        side_effect=spend_temp_knowledge,
    )

    # Setup
    initial_coins = 10
    initial_knowledge = 1
    player_state = replace(
        player_state_fixture,
        workers=[base_worker],
        coins=initial_coins,
        temporary_knowledge=initial_knowledge,
    )
    game_state = replace(game_state_fixture, players=[player_state])
    location_id = "ACADEMY_1"  # Requires 1 RED seal
    chosen_scroll_row = 1  # Cost 2
    chosen_seal_index = 2  # GREEN Seal
    worker_id = base_worker.worker_id
    # personal_board_cost = 1 # Unused variable
    expected_total_cost = 0 + 2 + 1  # Placement + Scroll + Board

    updated_state = perform_academy_action(
        game_state,
        0,
        worker_id,
        location_id,
        chosen_scroll_row,
        chosen_seal_index,
        True,
        all_game_data_fixture,
    )

    # Assertions on the returned state
    final_player_state = updated_state.players[0]
    final_worker_state = final_player_state.workers[0]

    assert final_player_state.coins == initial_coins - expected_total_cost
    assert (
        final_player_state.temporary_knowledge
        == initial_knowledge - expected_temp_knowledge_cost
    )
    assert final_worker_state.is_placed
    assert final_worker_state.seals.get(SealColor.GREEN) == 1
    assert final_worker_state.seal_slots_filled == 1
    assert updated_state.main_board_workers[location_id] == [(0, worker_id)]
    assert updated_state.academy_seals[chosen_scroll_row - 1][chosen_seal_index] is None


def test_perform_academy_action_valid_with_placement_penalty(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    """Test a successful academy action with a placement penalty."""
    expected_placement_penalty = 1
    # Patch dependencies using mocker
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 0)
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty",
        return_value=expected_placement_penalty,
    )
    mocker.patch("src.dj_engine.engine_utils.can_afford", return_value=True)
    mocker.patch("src.dj_engine.engine_utils.spend_coins", side_effect=spend_coins)
    mocker.patch(
        "src.dj_engine.engine_utils.spend_temp_knowledge",
        side_effect=spend_temp_knowledge,
    )

    # Setup
    initial_coins = 10
    initial_knowledge = 1
    worker = replace(base_worker, seals={SealColor.RED: 1})
    player_state = replace(
        player_state_fixture,
        workers=[worker],
        coins=initial_coins,
        temporary_knowledge=initial_knowledge,
    )
    game_state = replace(
        game_state_fixture,
        players=[player_state],
        main_board_workers={"ACADEMY_1": [(1, 101)]},
    )
    location_id = "ACADEMY_1"
    chosen_scroll_row = 1  # Cost 2
    chosen_seal_index = 0  # RED Seal
    worker_id = worker.worker_id
    # personal_board_cost = 1 # Unused variable
    expected_total_cost = expected_placement_penalty + 2 + 1

    updated_state = perform_academy_action(
        game_state,
        0,
        worker_id,
        location_id,
        chosen_scroll_row,
        chosen_seal_index,
        False,
        all_game_data_fixture,
    )

    # Assertions on the returned state
    final_player_state = updated_state.players[0]
    final_worker_state = final_player_state.workers[0]

    assert final_player_state.coins == initial_coins - expected_total_cost
    assert final_player_state.temporary_knowledge == initial_knowledge  # Unchanged
    assert final_worker_state.is_placed
    assert (
        final_worker_state.seals.get(SealColor.RED) == 2
    )  # FIXED: Expect 2 (started with 1, gained 1)
    assert final_worker_state.seal_slots_filled == 1
    assert updated_state.main_board_workers[location_id] == [(1, 101), (0, worker_id)]
    assert updated_state.academy_seals[chosen_scroll_row - 1][chosen_seal_index] is None


# --- Tests raising exceptions: No need to patch spend functions ---


def test_perform_academy_action_invalid_wrong_player(
    mocker: Any, game_state_fixture: GameState, all_game_data_fixture: AllGameData
) -> None:
    # No engine_utils patching needed as error occurs before calls
    game_state = replace(
        game_state_fixture, current_player_index=1
    )  # Player 0 is trying
    with pytest.raises(InvalidActionError, match="not Player 0's turn"):
        perform_academy_action(
            game_state, 0, 1, "ACADEMY_1", 1, 0, False, all_game_data_fixture
        )


def test_perform_academy_action_invalid_worker_not_found(
    mocker: Any, game_state_fixture: GameState, all_game_data_fixture: AllGameData
) -> None:
    # No patching needed
    with pytest.raises(InvalidActionError, match="Worker 99 not found"):
        perform_academy_action(
            game_state_fixture, 0, 99, "ACADEMY_1", 1, 0, False, all_game_data_fixture
        )


def test_perform_academy_action_invalid_worker_placed(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    # No patching needed
    worker = replace(base_worker, is_placed=True)
    player_state = replace(player_state_fixture, workers=[worker])
    game_state = replace(game_state_fixture, players=[player_state])
    with pytest.raises(InvalidActionError, match="already been placed"):
        perform_academy_action(
            game_state,
            0,
            worker.worker_id,
            "ACADEMY_1",
            1,
            0,
            False,
            all_game_data_fixture,
        )


def test_perform_academy_action_invalid_location_id(
    mocker: Any, game_state_fixture: GameState, all_game_data_fixture: AllGameData
) -> None:
    # No patching needed
    with pytest.raises(InvalidActionError, match="Invalid location ID: BOGUS"):
        perform_academy_action(
            game_state_fixture, 0, 1, "BOGUS", 1, 0, False, all_game_data_fixture
        )


def test_perform_academy_action_invalid_location_type(
    mocker: Any, game_state_fixture: GameState, all_game_data_fixture: AllGameData
) -> None:
    # No patching needed
    # Add a non-academy location to the data
    non_academy_loc = BoardActionLocation(
        id="EXPLORE_1",
        action_type="EXPLORE",
        diary_type="MAIN",
        placement_type="SQUARE",
        wax_seal_requirements={},
        base_actions=[],
        distinction_bonuses={},
    )
    all_game_data = replace(
        all_game_data_fixture,
        main_board_actions=all_game_data_fixture.main_board_actions
        | {"EXPLORE_1": non_academy_loc},
    )
    with pytest.raises(InvalidActionError, match="not an Academy action location"):
        perform_academy_action(
            game_state_fixture, 0, 1, "EXPLORE_1", 1, 0, False, all_game_data
        )


@pytest.mark.parametrize(
    "row, index, error_match",
    [
        (0, 0, "Invalid scroll row: 0"),
        (5, 0, "Invalid scroll row: 5"),
        (1, -1, "Invalid seal index: -1"),
        (1, 3, "Invalid seal index: 3"),
    ],
)
def test_perform_academy_action_invalid_scroll_coords(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    row: int,
    index: int,
    error_match: str,
) -> None:
    # No patching needed
    with pytest.raises(InvalidActionError, match=error_match):
        perform_academy_action(
            game_state_fixture,
            0,
            1,
            "ACADEMY_1",
            row,
            index,
            False,
            all_game_data_fixture,
        )


def test_perform_academy_action_invalid_seal_taken(
    mocker: Any, game_state_fixture: GameState, all_game_data_fixture: AllGameData
) -> None:
    # No patching needed
    # Remove a seal
    game_state = replace(game_state_fixture)
    game_state.academy_seals[0][0] = None  # Take seal at row 1, index 0
    with pytest.raises(InvalidActionError, match="No seal available"):
        perform_academy_action(
            game_state, 0, 1, "ACADEMY_1", 1, 0, False, all_game_data_fixture
        )


def test_perform_academy_action_invalid_seal_req_no_temp(
    mocker: Any, game_state_fixture: GameState, all_game_data_fixture: AllGameData
) -> None:
    # Patch check_wax_seal_req to simulate failure
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(False, 1)
    )
    with pytest.raises(InvalidActionError, match="does not meet requirements"):
        perform_academy_action(
            game_state_fixture, 0, 1, "ACADEMY_1", 1, 0, False, all_game_data_fixture
        )


def test_perform_academy_action_invalid_seal_req_use_temp_false(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    # Patch check_wax_seal_req to simulate needing temp knowledge
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 1)
    )
    # --- ADDED Setup ---
    player_state = replace(
        player_state_fixture, workers=[base_worker], temporary_knowledge=1
    )
    game_state = replace(game_state_fixture, players=[player_state])
    worker_id = base_worker.worker_id
    location_id = "ACADEMY_1"
    # --- End Setup ---
    with pytest.raises(
        InvalidActionError,
        match="Temp knowledge .* needed, but 'use_temp_knowledge' is False.",
    ):
        perform_academy_action(
            game_state, 0, worker_id, location_id, 1, 0, False, all_game_data_fixture
        )


def test_perform_academy_action_invalid_worker_full(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    # Patch check_wax_seal_req to simulate success (doesn't matter)
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 0)
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty", return_value=0
    )
    # --- ADDED Setup ---
    worker = replace(
        base_worker,
        seals={SealColor.RED: 1, SealColor.BLUE: 1, SealColor.GREEN: 1},
        seal_slots_filled=3,
    )
    player_state = replace(player_state_fixture, workers=[worker], coins=10)
    game_state = replace(game_state_fixture, players=[player_state])
    location_id = "ACADEMY_1"
    chosen_scroll_row = (
        1  # FIXED: Changed from 2 to 1, as only scroll 1 exists in fixture
    )
    chosen_seal_index = 0
    worker_id = worker.worker_id
    # --- End Setup ---
    with pytest.raises(InvalidActionError, match="cannot hold more seals"):
        perform_academy_action(
            game_state,
            0,
            worker_id,
            location_id,
            chosen_scroll_row,
            chosen_seal_index,
            False,
            all_game_data_fixture,
        )


def test_perform_academy_action_insufficient_coins(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    # Patch upstream checks
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 0)
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty", return_value=0
    )
    # Patch can_afford to cause the failure
    mocker.patch("src.dj_engine.engine_utils.can_afford", return_value=False)
    # --- ADDED Setup ---
    worker = replace(base_worker, seals={SealColor.RED: 1})
    scroll_cost = all_game_data_fixture.academy_scrolls[1].cost  # 2
    # Handle potential None for personal_board
    assert all_game_data_fixture.personal_board is not None, (
        "Personal board definition is missing in fixture"
    )
    board_cost = (
        all_game_data_fixture.personal_board.worker_rows[0].seal_slots[0].placement_cost
    )  # 1
    total_cost = 0 + scroll_cost + board_cost  # 3
    player_state = replace(
        player_state_fixture, workers=[worker], coins=total_cost - 1
    )  # 2 coins
    game_state = replace(game_state_fixture, players=[player_state])
    worker_id = worker.worker_id
    location_id = "ACADEMY_1"
    # --- End Setup ---
    with pytest.raises(InsufficientResourcesError, match="cannot afford cost"):
        perform_academy_action(
            game_state, 0, worker_id, location_id, 1, 0, False, all_game_data_fixture
        )


def test_perform_academy_action_insufficient_temp_knowledge(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    # Patch upstream checks
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 1)
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty", return_value=0
    )
    mocker.patch("src.dj_engine.engine_utils.can_afford", return_value=True)
    # --- ADDED Setup ---
    player_state = replace(
        player_state_fixture, workers=[base_worker], temporary_knowledge=0
    )
    game_state = replace(game_state_fixture, players=[player_state])
    worker_id = base_worker.worker_id
    location_id = "ACADEMY_1"
    # --- End Setup ---
    with pytest.raises(InsufficientResourcesError, match="needs .* temp knowledge"):
        perform_academy_action(
            game_state, 0, worker_id, location_id, 1, 0, True, all_game_data_fixture
        )


# Potential GameError tests
def test_perform_academy_action_game_error_missing_scroll_data(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 0)
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty", return_value=0
    )
    # --- ADDED Setup ---
    worker = replace(base_worker, seals={SealColor.RED: 1})
    player_state = replace(player_state_fixture, workers=[worker])
    game_state = replace(game_state_fixture, players=[player_state])
    all_game_data = replace(all_game_data_fixture, academy_scrolls={})
    worker_id = worker.worker_id
    location_id = "ACADEMY_1"
    # --- End Setup ---
    with pytest.raises(GameError, match="Could not find scroll data for row 1"):
        perform_academy_action(
            game_state, 0, worker_id, location_id, 1, 0, False, all_game_data
        )


def test_perform_academy_action_game_error_missing_personal_board(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 0)
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty", return_value=0
    )
    # --- ADDED Setup ---
    worker = replace(base_worker, seals={SealColor.RED: 1})
    player_state = replace(player_state_fixture, workers=[worker])
    game_state = replace(game_state_fixture, players=[player_state])
    all_game_data = replace(all_game_data_fixture, personal_board=None)
    worker_id = worker.worker_id
    location_id = "ACADEMY_1"
    # --- End Setup ---
    with pytest.raises(GameError, match="Personal board definition not loaded"):
        perform_academy_action(
            game_state, 0, worker_id, location_id, 1, 0, False, all_game_data
        )


def test_perform_academy_action_game_error_missing_worker_row_def(
    mocker: Any,
    game_state_fixture: GameState,
    all_game_data_fixture: AllGameData,
    player_state_fixture: PlayerState,
    base_worker: WorkerState,
) -> None:
    mocker.patch(
        "src.dj_engine.engine_utils.check_wax_seal_req", return_value=(True, 0)
    )
    mocker.patch(
        "src.dj_engine.engine_utils.calculate_placement_penalty", return_value=0
    )
    # --- ADDED Setup ---
    worker = replace(base_worker, seals={SealColor.RED: 1}, row_index=99)
    player_state = replace(player_state_fixture, workers=[worker])
    game_state = replace(game_state_fixture, players=[player_state])
    worker_id = worker.worker_id
    location_id = "ACADEMY_1"
    # --- End Setup ---
    with pytest.raises(GameError, match="Internal Error: No board def for row"):
        perform_academy_action(
            game_state, 0, worker_id, location_id, 1, 0, False, all_game_data_fixture
        )
