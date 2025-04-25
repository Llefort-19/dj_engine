import random

from .constants import INITIAL_STAMP_COUNT, PlayerColor, SealColor
from .data_loader import (
    # CORRESPONDENCES_TILES_DATA, # Removed
    # ISLAND_A_TRACK_DATA, # Removed
    # ISLAND_B_TRACK_DATA, # Removed
    # ISLAND_C_TRACK_DATA, # Removed
    # OBJECTIVE_TILES_DATA, # Removed
    # OCEAN_TRACK_DATA, # Removed
    # SPECIAL_ACTION_TILES_DATA, # Removed
    # SPECIES_DATA, # Removed
    load_all_data,  # Keep this one
)
from .game_state import GameState
from .player import PlayerState, WorkerState


def setup_game() -> GameState:
    """
    Initializes the GameState for a new 2-player game of Darwin's Journey.

    Sets up player boards, initial resources, determines turn order,
    and prepares game components like decks and tracks based on rulebook Phase 3.
    """
    # --- Phase 1/2: Load Data & Initialize Base State ---
    # Load data explicitly via function call
    all_game_data = load_all_data()

    player_count = 2  # Hardcoded for 2 players for now
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
            for stack_index in range(3)  # Stacks 0, 1, 2
        }

        player_state = PlayerState(
            player_index=i,
            player_color=player_color,
            workers=workers,
            coins=4,  # Rule 5
            temporary_knowledge=1,  # Rule 6
            tents_available=5,  # Rule 1/2A
            stamps_available=stamps_available,  # Rule 1/2A
            # Other fields will default or be set later
        )
        player_states.append(player_state)

    game_state.players = player_states

    # --- Rule 12/13: Place Starting Explorers ---
    for player_state in game_state.players:
        player_state.explorers_placed["A"] = "IA0"  # Place on Island A start
        player_state.explorers_available -= 1  # Use one explorer

    # --- Rule 1/2B: Determine First Player & Turn Order ---
    # For now, simple sequential order starting from index 0
    # TODO: Implement random first player and clockwise order later if needed
    game_state.turn_order = list(range(player_count))
    game_state.first_player_marker_index = 0
    game_state.current_player_index = game_state.turn_order[0]

    # --- Phase 3 Setup Steps (To be continued) ---

    # Rule 12: Special Action Tile Setup
    special_action_locations = [
        "SPECIAL_ACTION_TL",
        "SPECIAL_ACTION_ML",
        "SPECIAL_ACTION_BL",
        "SPECIAL_ACTION_TR",
        "SPECIAL_ACTION_MR",
        "SPECIAL_ACTION_BR",
    ]
    # Access via returned data
    all_special_tiles = list(all_game_data["special_action_tiles"].values())
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
    # Access via returned data
    all_correspondence_tiles = list(all_game_data["correspondences_tiles"].values())
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
    for i in range(12):  # Place 12 seals
        seal_to_place = academy_seal_pool.pop()
        scroll_row = i // 3
        game_state.academy_seals[scroll_row].append(seal_to_place)
        # Decrement from the available supply
        game_state.available_seals[seal_to_place] -= 1

    # Rule 9: Objective Setup
    # Access via returned data
    all_objective_tiles = list(all_game_data["objective_tiles"].values())
    random.shuffle(all_objective_tiles)

    # Filter all objectives into starting and main piles based on the 'starting' flag
    starting_objectives = [
        obj for obj in all_objective_tiles if obj.starting
    ]  # Reverted to list comp

    main_objectives = [obj for obj in all_objective_tiles if not obj.starting]

    # Populate main decks (from non-starting objectives)
    game_state.objective_deck_silver = [
        obj
        for obj in main_objectives
        if obj.type == "SILVER"  # Uppercase
    ]
    game_state.objective_deck_gold = [
        obj
        for obj in main_objectives
        if obj.type == "GOLD"  # Uppercase
    ]

    # Filter starting objectives by type
    starting_silver = [
        obj for obj in starting_objectives if obj.type == "SILVER"
    ]  # Uppercase
    starting_gold = [
        obj for obj in starting_objectives if obj.type == "GOLD"
    ]  # Uppercase

    # Assign starting objectives
    # (Deals first available pair, one silver/one gold if possible)
    assigned_silver = 0
    assigned_gold = 0
    for i in range(player_count):
        # Assign Silver
        if assigned_silver < len(starting_silver):
            game_state.players[i].objective_tiles_in_reserve.append(
                starting_silver[assigned_silver]
            )
            assigned_silver += 1
        else:
            # This case should not happen with correct data, but log if it does
            print(f"Warning: Ran out of starting silver objectives for player {i}")

        # Assign Gold
        if assigned_gold < len(starting_gold):
            game_state.players[i].objective_tiles_in_reserve.append(
                starting_gold[assigned_gold]
            )
            assigned_gold += 1
        else:
            # This case should not happen with correct data, but log if it does
            print(f"Warning: Ran out of starting gold objectives for player {i}")

    # Setup Objective Display (Draw 2 silver, 2 gold from main decks)
    for _ in range(2):
        if game_state.objective_deck_silver:
            game_state.objective_display_silver.append(
                game_state.objective_deck_silver.pop(0)  # Draw from top
            )
        if game_state.objective_deck_gold:
            game_state.objective_display_gold.append(
                game_state.objective_deck_gold.pop(0)  # Draw from top
            )

    # --- Rule 16: Specimen Placement on Tracks & Museum ---
    # Access via returned data
    eligible_track_spaces: list[str] = []
    all_track_data_sources = [
        all_game_data["island_a_track"],
        all_game_data["island_b_track"],
        all_game_data["island_c_track"],
        all_game_data["ocean_track"],
    ]
    for track_data in all_track_data_sources:
        for track_space in track_data.values():
            if track_space.has_specimen:
                # Add assertion to help mypy and catch potential runtime errors
                assert isinstance(track_space.id, str), (
                    f"Track space ID should be str, got {type(track_space.id)}"
                )
                eligible_track_spaces.append(track_space.id)

    # (Shuffle Specimens)
    # Access via returned data
    species_data = all_game_data["species"]
    all_specimen_token_ids = list(species_data.keys())
    random.shuffle(all_specimen_token_ids)

    # (Place on Tracks)
    specimens_for_tracks = all_specimen_token_ids[:10]
    game_state.placed_specimens = {
        track_id: specimen_id
        for track_id, specimen_id in zip(eligible_track_spaces, specimens_for_tracks)
    }

    # (Identify Leftovers & Mark Museum Slots)
    specimen_leftovers = all_specimen_token_ids[10:]
    for token_id in specimen_leftovers:
        species_info = species_data[token_id]
        museum_slot_key = (species_info.museum_row, species_info.museum_col)
        # Mark the slot as occupied for scoring purposes, no immediate reward
        game_state.museum_state[museum_slot_key] = token_id

    # Rule 16: Museum Coins (Already defaults to empty set in GameState)
    # game_state.museum_coins_taken = set() # Initialization done by default_factory

    # Rule 3: Place HMS Beagle (Already defaulted in GameState)
    # Rule 8: Museum Setup (Partially handled by specimen leftovers above)

    # Rule 15: Beagle Goal Setup (Added)
    all_beagle_goals = list(all_game_data["beagles_goals"].values())
    random.shuffle(all_beagle_goals)
    game_state.beagle_goals_in_play = all_beagle_goals[:5]
    game_state.beagle_goals_completed = [False] * 5  # Initialize completion tracking

    # --- Simplified Crew Card Dealing & Starting Seal Placement ---
    all_crew_cards = list(all_game_data["crew_cards"].values())
    random.shuffle(all_crew_cards)

    dealt_card_index = 0
    for i in range(player_count):
        player_state = game_state.players[i]
        cards_dealt_to_player = []

        # Deal 3 cards
        for card_deal_num in range(3):
            if dealt_card_index < len(all_crew_cards):
                card = all_crew_cards[dealt_card_index]
                cards_dealt_to_player.append(card)
                player_state.crew_cards_assigned_starting.append(card.id)

                # Apply starting seal to corresponding worker (0, 1, 2)
                if card_deal_num < len(player_state.workers):
                    worker = player_state.workers[card_deal_num]
                    seal_color = card.starting_seal_color

                    # Add seal to worker seals dict
                    worker.seals[seal_color] = worker.seals.get(seal_color, 0) + 1
                    worker.seal_slots_filled += 1
                else:
                    # Should not happen with 3 cards and 4+ workers
                    print(
                        f"Warn: Cannot assign seal from card {card.id} to worker "
                        f"{card_deal_num} for player {i} (worker not found)"
                    )

                dealt_card_index += 1
            else:
                # Should not happen with enough crew cards
                print(f"Warning: Ran out of crew cards to deal to player {i}")
                break  # Stop dealing to this player if out of cards

    # Return the initialized game state
    return game_state


# Example usage (can be removed later)
if __name__ == "__main__":
    initial_game_state = setup_game()
    print("Initial Game State (Partial):")
    print(initial_game_state)
    print("\nPlayer 0 State:")
    print(initial_game_state.players[0])
    print("\nPlayer 1 State:")
    print(initial_game_state.players[1])
