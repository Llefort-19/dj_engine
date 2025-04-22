import random

from .constants import INITIAL_STAMP_COUNT, PlayerColor, SealColor
from .data_loader import (
    CORRESPONDENCES_TILES_DATA,
    OBJECTIVE_TILES_DATA,
    SPECIAL_ACTION_TILES_DATA,
    STARTING_OBJECTIVES_TILES_DATA,
)
from .game_state import GameState
from .player import PlayerState, WorkerState


def setup_game() -> GameState:
    """
    Initializes the GameState for a new 2-player game of Darwin's Journey.

    Sets up player boards, initial resources, determines turn order,
    and prepares game components like decks and tracks based on rulebook Phase 3.
    """
    player_count = 2 # Hardcoded for 2 players for now

    # Load all static game data first
    # all_data = load_all_data() # TODO: Use this later
    # TODO: Use the data loaded in `all_data` instead of global vars later

    game_state = GameState()

    # --- Rule 1/2A: Setup Players ---
    player_colors = [PlayerColor.BLUE, PlayerColor.GREEN]

    player_states: list[PlayerState] = []
    for i in range(player_count):
        player_color = player_colors[i]

        # Initialize workers (Rule 1/2A)
        workers = [
            WorkerState(worker_id=worker_id, row_index=row)
            for worker_id, row in enumerate(range(1, 5))  # IDs 0-3, Rows 1-4
        ]

        # Initialize stamps (Rule 1/2A)
        stamps_available = {
            stack_index: INITIAL_STAMP_COUNT
            for stack_index in range(3) # Stacks 0, 1, 2
        }

        player_state = PlayerState(
            player_index=i,
            player_color=player_color,
            workers=workers,
            coins=4,  # Rule 5
            temporary_knowledge=1,  # Rule 6
            tents_available=5,  # Rule 1/2A
            stamps_available=stamps_available, # Rule 1/2A
            # Other fields will default or be set later
        )
        player_states.append(player_state)

    game_state.players = player_states

    # --- Rule 1/2B: Determine First Player & Turn Order ---
    # For now, simple sequential order starting from index 0
    # TODO: Implement random first player and clockwise order later if needed
    game_state.turn_order = list(range(player_count))
    game_state.first_player_marker_index = 0
    game_state.current_player_index = game_state.turn_order[0]

    # --- Phase 3 Setup Steps (To be continued) ---

    # Rule 12: Special Action Tile Setup
    special_action_locations = [
        "SPECIAL_ACTION_TL", "SPECIAL_ACTION_ML", "SPECIAL_ACTION_BL",
        "SPECIAL_ACTION_TR", "SPECIAL_ACTION_MR", "SPECIAL_ACTION_BR"
    ]
    all_special_tiles = list(SPECIAL_ACTION_TILES_DATA.values())
    random.shuffle(all_special_tiles)
    # Assign the first 6 shuffled tiles to the defined locations
    game_state.special_action_tiles_setup = {
        loc_id: tile
        for loc_id, tile in zip(special_action_locations, all_special_tiles[:6])
    }

    # Rule 3: Neutral Lenses unlock top row special actions
    game_state.unlocked_locations.add("SPECIAL_ACTION_TL")
    game_state.unlocked_locations.add("SPECIAL_ACTION_TR")

    # Rule 10: Correspondence Setup
    all_correspondence_tiles = list(CORRESPONDENCES_TILES_DATA.values())
    random.shuffle(all_correspondence_tiles)
    game_state.correspondence_tiles_in_play = all_correspondence_tiles[:3]
    # Initialize stamp tracking: {tile_index: {player_index: stamp_count}}
    game_state.correspondence_stamps = {i: {} for i in range(3)}

    # Rule 4: Seal Supply
    game_state.available_seals = {
        SealColor.BLUE: 12,
        SealColor.GREEN: 12,
        SealColor.YELLOW: 12,
        SealColor.RED: 12,
        SealColor.SPECIAL: 12,
    }

    # Rule 7: Academy Setup
    academy_seal_pool = (
        [SealColor.BLUE] * 12
        + [SealColor.GREEN] * 12
        + [SealColor.YELLOW] * 12
        + [SealColor.RED] * 12
    )
    random.shuffle(academy_seal_pool)

    game_state.academy_seals = [[], [], [], []]  # 4 scrolls
    for i in range(12): # Place 12 seals
        seal_to_place = academy_seal_pool.pop()
        scroll_row = i // 3
        game_state.academy_seals[scroll_row].append(seal_to_place)
        # Decrement from the available supply
        game_state.available_seals[seal_to_place] -= 1

    # Rule 9: Objective Setup
    all_objectives = list(OBJECTIVE_TILES_DATA.values())
    starting_objectives = list(STARTING_OBJECTIVES_TILES_DATA.values())
    random.shuffle(all_objectives)
    random.shuffle(starting_objectives)

    # Separate deck objectives by type
    game_state.objective_deck_silver = [
        obj for obj in all_objectives if obj.type == "silver"
    ]
    game_state.objective_deck_gold = [
        obj for obj in all_objectives if obj.type == "gold"
    ]

    # Separate starting objectives by type
    starting_silver = [obj for obj in starting_objectives if obj.type == "silver"]
    starting_gold = [obj for obj in starting_objectives if obj.type == "gold"]

    # Assign starting objectives (Simplified: deals first available pair to players)
    # TODO: Implement actual draft if required later
    assigned_starting_silver = 0
    assigned_starting_gold = 0
    for i in range(player_count):
        if assigned_starting_silver < len(starting_silver):
            game_state.players[i].objective_tiles_in_reserve.append(
                starting_silver[assigned_starting_silver]
            )
            assigned_starting_silver += 1
        else:
            # Handle potential lack of starting objectives gracefully
            print(f"Warning: Not enough starting silver objectives for player {i}")

        if assigned_starting_gold < len(starting_gold):
            game_state.players[i].objective_tiles_in_reserve.append(
                starting_gold[assigned_starting_gold]
            )
            assigned_starting_gold += 1
        else:
            print(f"Warning: Not enough starting gold objectives for player {i}")

    # Setup Objective Display (Draw 2 silver, 2 gold)
    for _ in range(2):
        if game_state.objective_deck_silver:
            game_state.objective_display_silver.append(
                game_state.objective_deck_silver.pop(0) # Draw from top
            )
        if game_state.objective_deck_gold:
            game_state.objective_display_gold.append(
                game_state.objective_deck_gold.pop(0) # Draw from top
            )

    # Rule 3: Place HMS Beagle (Already defaulted in GameState)
    # Rule 8: Museum Setup
    # Rule 11: Beagle Goal Setup

    # Return the partially initialized game state
    return game_state

# Example usage (can be removed later)
if __name__ == "__main__":
    initial_game_state = setup_game()
    print("Initial Game State (Partial):")
    print(initial_game_state)
    print("\\nPlayer 0 State:")
    print(initial_game_state.players[0])
    print("\\nPlayer 1 State:")
    print(initial_game_state.players[1])
