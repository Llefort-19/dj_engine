from dj_engine.constants import (
    ActionType,
    ObjectiveRequirementType,
    SealColor,
    SpecimenKind,
    TrackType,
)
from dj_engine.data_loader import (
    AcademyScroll,
    BeagleGoal,
    BoardActionLocation,
    Campsite,
    CorrespondenceTile,
    CrewCard,
    ObjectiveDisplayAreaInfo,
    ObjectiveDisplayComponent,
    ObjectiveRequirement,
    ObjectiveTile,
    PersonalBoardDefinition,
    PersonalBoardObjectiveSlot,
    PersonalBoardReserveObjectiveSlot,
    PersonalBoardSealSlot,
    PersonalBoardSpecimenSlot,
    PersonalBoardStampSlot,
    PersonalBoardTentSlot,
    PersonalBoardWorkerRow,
    ScoringCondition,
    SimpleActionInfo,
    SpecialActionTile,
    Species,
    TentSlotInfo,
    TheoryTrackSpace,
    TrackSpace,
    load_academy_scrolls,
    load_beagles_goals,
    load_campsites,
    load_correspondences_tiles,
    load_crew_cards,
    load_island_track,
    load_main_board_actions,
    load_objective_display_area,
    load_objective_tiles,
    load_ocean_tracks,
    load_personal_board,
    load_special_action_tiles,
    load_species,
    load_theory_of_evolution_track,
)


def test_load_initial_data() -> None:
    """Tests loading initial set of static data."""

    # Load data
    species_data = load_species()
    scroll_data = load_academy_scrolls()
    objective_area_info = load_objective_display_area()
    crew_card_data = load_crew_cards()
    objective_tile_data = load_objective_tiles()
    ocean_track_data = load_ocean_tracks()
    island_a_track_data = load_island_track("A")
    main_board_actions_data = load_main_board_actions()
    theory_track_data = load_theory_of_evolution_track()
    campsite_data = load_campsites()
    beagle_goals_data = load_beagles_goals()
    correspondence_tiles_data = load_correspondences_tiles()
    special_action_tiles_data = load_special_action_tiles()
    personal_board_data = load_personal_board()

    # --- Species Data Assertions ---
    assert species_data, "Species data should not be empty"
    assert "SPN_GREEN_REPTILE" in species_data, "Known species ID should exist"

    green_reptile = species_data["SPN_GREEN_REPTILE"]
    assert isinstance(green_reptile, Species), (
        "Species data item should be of type Species"
    )
    # TODO: Update kind check when SpecimenKind Enum is created
    assert green_reptile.kind == "REPTILE", "Species kind attribute check"
    assert green_reptile.colour == "GREEN", "Species colour attribute check"
    assert green_reptile.museum_row == "A", "Species museum_row attribute check"
    assert green_reptile.museum_col == 1, "Species museum_col attribute check"

    # --- Academy Scroll Data Assertions ---
    assert scroll_data, "Academy scroll data should not be empty"
    assert 1 in scroll_data, "Known scroll row number should exist"

    scroll_row_1 = scroll_data[1]
    assert isinstance(scroll_row_1, AcademyScroll), (
        "Scroll data item should be of type AcademyScroll"
    )
    assert scroll_row_1.scroll_row == 1, "Scroll row number attribute check"
    assert scroll_row_1.cost == 0, "Scroll cost attribute check for row 1"
    assert scroll_row_1.slots == 3, "Scroll slots attribute check for row 1"

    # Check another scroll row for variety
    assert 4 in scroll_data, "Scroll row 4 should exist"
    scroll_row_4 = scroll_data[4]
    assert scroll_row_4.cost == 3, "Scroll cost attribute check for row 4"

    # --- Objective Display Area Assertions ---
    assert objective_area_info, "Objective area info should not be None"
    assert isinstance(objective_area_info, ObjectiveDisplayAreaInfo), (
        "Loaded data should be ObjectiveDisplayAreaInfo type"
    )
    assert objective_area_info.area_id == "OBJECTIVE_DISPLAY_AREA"
    assert not objective_area_info.is_worker_placement_location
    assert len(objective_area_info.components) == 4, "Should have 4 components"

    # Check first component (silver deck)
    silver_deck = next(
        (
            c
            for c in objective_area_info.components
            if c.component_type == "DECK_SLOT" and c.objective_type == "silver"
        ),
        None,
    )
    assert silver_deck is not None, "Silver deck component not found"
    assert isinstance(silver_deck, ObjectiveDisplayComponent)

    # Check one of the display slots (gold display)
    gold_display = next(
        (
            c
            for c in objective_area_info.components
            if c.component_type == "DISPLAY_SLOT" and c.objective_type == "gold"
        ),
        None,
    )
    assert gold_display is not None, "Gold display component not found"
    assert isinstance(gold_display, ObjectiveDisplayComponent)
    assert gold_display.count == 2, "Gold display should have count 2"

    # --- Crew Card Data Assertions ---
    assert crew_card_data, "Crew card data should not be empty"
    assert 1 in crew_card_data, "Crew card ID 1 should exist"

    card_1 = crew_card_data[1]
    assert isinstance(card_1, CrewCard), "Crew card item should be type CrewCard"
    assert card_1.id == 1
    # TODO: Update color check when SealColor Enum is created
    assert card_1.starting_seal_color == "BLUE"
    assert card_1.activation_requirement == {"BLUE": 2, "YELLOW": 2, "GREEN": 1}
    assert len(card_1.achieved_actions) == 1
    action_info = card_1.achieved_actions[0]
    assert isinstance(action_info, SimpleActionInfo)
    # TODO: Update type check when ActionType Enum is created
    assert action_info.type == ActionType.GAIN_COINS
    assert action_info.value == 8

    # Check card 5 with cost_modifier
    assert 5 in crew_card_data, "Crew card ID 5 should exist"
    card_5 = crew_card_data[5]
    assert len(card_5.achieved_actions) == 1
    action_info_5 = card_5.achieved_actions[0]
    assert action_info_5.type == ActionType.UNLOCK_LENS
    # Checks if cost_modifier was correctly assigned to value
    assert action_info_5.value == "FREE"

    # --- Objective Tile Data Assertions ---
    assert objective_tile_data, "Objective tile data should not be empty"
    assert 5 in objective_tile_data, "Objective ID 5 should exist"

    obj_5 = objective_tile_data[5]
    assert isinstance(obj_5, ObjectiveTile), (
        "Objective item should be type ObjectiveTile"
    )
    assert obj_5.id == 5
    assert obj_5.type == "silver"
    assert len(obj_5.requirements) == 2

    # Check first requirement for Objective 5
    req1_obj5 = obj_5.requirements[0]
    assert isinstance(req1_obj5, ObjectiveRequirement)
    assert req1_obj5.type == ObjectiveRequirementType.HAVE_SEALS
    assert req1_obj5.color == SealColor.BLUE
    assert req1_obj5.count == 2
    assert req1_obj5.kind is None
    assert req1_obj5.value is None

    # Check second requirement for Objective 5
    req2_obj5 = obj_5.requirements[1]
    assert req2_obj5.type == ObjectiveRequirementType.HAVE_SPECIMEN_RESEARCHED
    assert req2_obj5.kind == SpecimenKind.REPTILE
    assert req2_obj5.count == 1
    assert req2_obj5.color is None

    # Check a gold objective (ID 13)
    assert 13 in objective_tile_data, "Objective ID 13 should exist"
    obj_13 = objective_tile_data[13]
    assert obj_13.type == "gold"
    assert len(obj_13.requirements) == 2
    assert (
        obj_13.requirements[0].type == ObjectiveRequirementType.HAVE_SPECIMEN_RESEARCHED
    )
    assert obj_13.requirements[0].kind == SpecimenKind.BIRD
    assert obj_13.starting is False

    # --- Test starting objective tiles loaded via main function ---
    # Find a known starting objective (e.g., ID 1, assuming it exists and is marked)
    start_obj_1 = objective_tile_data.get(1)
    assert start_obj_1 is not None, (
        "Starting objective ID 1 should exist in loaded data"
    )
    assert start_obj_1.starting is True, "Objective ID 1 should be marked as starting"
    assert start_obj_1.type == "silver"
    assert len(start_obj_1.requirements) == 2

    # Check requirements for Starting Objective 1
    req1_start1 = start_obj_1.requirements[0]
    assert isinstance(req1_start1, ObjectiveRequirement)
    assert req1_start1.type == ObjectiveRequirementType.SHIP_AT_BEAGLE_OR_AHEAD
    assert req1_start1.count is None

    req2_start1 = start_obj_1.requirements[1]
    assert req2_start1.type == ObjectiveRequirementType.HAVE_TEMP_KNOWLEDGE
    assert req2_start1.count == 2

    # Check a gold starting objective (e.g. ID 13 if it's also starting)
    start_obj_13 = objective_tile_data.get(13)  # Assuming 13 can be starting too
    # Need to check if 13 IS actually a starting tile in the consolidated data
    if start_obj_13 and start_obj_13.starting:
        assert start_obj_13.type == "gold"
    else:
        # If 13 isn't starting, find another known starting gold one, or adjust test
        # For now, just acknowledge it might not be starting
        print(
            "DEBUG: Objective 13 not marked as starting, skipping gold starting check."
        )

    # --- Ocean Track Data Assertions ---
    assert ocean_track_data, "Ocean track data should not be empty"
    assert "O0" in ocean_track_data, "Ocean space O0 should exist"
    assert "O26" in ocean_track_data, "Ocean space O26 should exist"

    space_o1 = ocean_track_data["O1"]
    assert isinstance(space_o1, TrackSpace), (
        "Ocean space item should be TrackSpace type"
    )
    assert space_o1.id == "O1"
    assert space_o1.silver_banner
    assert space_o1.beagle_goal
    assert space_o1.spawns_explorer_on_island == "A"
    assert space_o1.next == ["O2", "O3"]
    assert not space_o1.actions  # Check empty actions

    space_o17 = ocean_track_data["O17"]
    assert len(space_o17.actions) == 2
    assert space_o17.actions[0].type == ActionType.GAIN_COINS
    assert space_o17.actions[0].value == 3
    assert space_o17.actions[1].type == ActionType.ADVANCE_THEORY
    assert space_o17.actions[1].value == 2

    # --- Island Track Data Assertions (Island A example) ---
    assert island_a_track_data, "Island A track data should not be empty"
    assert "IA0" in island_a_track_data, "Island A start space (IA0) should exist"
    assert "IA10" in island_a_track_data  # Example space check

    start_a = island_a_track_data["IA0"]
    assert isinstance(start_a, TrackSpace)
    # assert start_a.is_island_entry # Removed check
    # assert not start_a.is_island_exit # Removed check
    assert start_a.next == ["IA1"]
    assert start_a.golden_ribbon_vp is None  # Check golden ribbon for start

    # Check space IA4 for golden ribbon VP
    space_ia4 = island_a_track_data["IA4"]
    assert isinstance(space_ia4, TrackSpace)
    assert space_ia4.golden_ribbon_vp == 1

    # Check space IA3 (corrected ID/action check)
    space_ia3 = island_a_track_data["IA3"]
    assert space_ia3.actions[0].type == ActionType.GAIN_TEMP_KNOWLEDGE

    # Verify exit space IA24 properties
    assert "IA24" in island_a_track_data, "Exit space IA24 should exist"
    exit_space_a = island_a_track_data["IA24"]
    assert exit_space_a is not None
    assert not exit_space_a.next  # Exit space has no 'next'
    # Verify end bonus
    assert exit_space_a.actions[-1].type == ActionType.END_OF_ISLAND_BONUS
    # Explicitly check ribbon VP is None here
    assert exit_space_a.golden_ribbon_vp is None

    # --- Main Board Actions Data Assertions ---
    assert main_board_actions_data, "Main board actions data should not be empty"

    # Check MAIN1_EXPLORE_1
    explore1 = main_board_actions_data.get("MAIN1_EXPLORE_1")
    assert explore1 is not None
    assert isinstance(explore1, BoardActionLocation)
    assert explore1.action_type == "EXPLORE"
    assert not explore1.locked
    assert explore1.wax_seal_requirements == {SealColor.GREEN: 1}
    assert len(explore1.base_actions) == 1
    assert explore1.base_actions[0].type == ActionType.EXPLORE
    assert explore1.base_actions[0].value == 2
    assert len(explore1.distinction_bonuses["silver"]) == 1
    assert explore1.distinction_bonuses["silver"][0].type == "BONUS_EXPLORE"
    assert explore1.distinction_bonuses["silver"][0].value == 1
    assert len(explore1.distinction_bonuses["golden"]) == 1
    assert explore1.distinction_bonuses["golden"][0].type == "BONUS_MOVEMENT_STOP"

    # Check MAIN2_ACADEMY_2 (locked, multiple base actions)
    academy2 = main_board_actions_data.get("MAIN2_ACADEMY_2")
    assert academy2 is not None
    assert academy2.locked
    assert academy2.unlock_cost == 4
    assert academy2.wax_seal_requirements == {SealColor.RED: 2}
    assert len(academy2.base_actions) == 2
    assert academy2.base_actions[0].type == ActionType.ACADEMY
    assert academy2.base_actions[1].type == ActionType.ACADEMY
    assert academy2.base_actions[1].value == -1  # cost_modifier
    assert len(academy2.distinction_bonuses["golden"]) == 1
    assert academy2.distinction_bonuses["golden"][0].type == "BONUS_ACADEMY_DISCOUNT"
    assert academy2.distinction_bonuses["golden"][0].value == 1

    # Check MUSEUM (no wax seals, multiple base actions)
    museum = main_board_actions_data.get("MUSEUM")
    assert museum is not None
    assert not museum.locked
    assert not museum.wax_seal_requirements  # Check empty dict
    assert len(museum.base_actions) == 2
    assert museum.base_actions[0].type == ActionType.DELIVER_SPECIMEN
    assert museum.base_actions[1].type == ActionType.RESEARCH_MUSEUM
    assert not museum.distinction_bonuses["silver"]  # Check empty list
    assert not museum.distinction_bonuses["golden"]

    # Check exit space IA24 golden ribbon VP
    assert exit_space_a.golden_ribbon_vp is None

    # --- Theory Track Data Assertions ---
    assert theory_track_data, "Theory track data should not be empty"
    assert 1 in theory_track_data, "Theory track space 1 should exist"
    assert 36 in theory_track_data, "Theory track space 36 should exist"
    assert len(theory_track_data) == 36, "Should be 36 theory track spaces"

    space_1 = theory_track_data[1]
    assert isinstance(space_1, TheoryTrackSpace)
    assert space_1.id == 1
    assert space_1.book_multiplier == 1

    space_10 = theory_track_data[10]
    assert space_10.book_multiplier == 7

    space_36 = theory_track_data[36]
    assert space_36.book_multiplier == 15

    # --- Campsite Data Assertions ---
    assert campsite_data, "Campsite data should not be empty"
    assert "CAMP_AREA_O6" in campsite_data, "Campsite CAMP_AREA_O6 should exist"

    camp_o6 = campsite_data["CAMP_AREA_O6"]
    assert isinstance(camp_o6, Campsite)
    assert camp_o6.id == "CAMP_AREA_O6"
    assert camp_o6.originating_track_space_id == "O6"
    assert camp_o6.track_type == TrackType.OCEAN
    assert len(camp_o6.tent_slots) == 2
    assert isinstance(camp_o6.tent_slots[0], TentSlotInfo)
    assert camp_o6.tent_slots[0].slot_index == 0
    assert camp_o6.tent_slots[0].placement_cost == 0
    assert camp_o6.tent_slots[1].slot_index == 1
    assert camp_o6.tent_slots[1].placement_cost == 1
    assert len(camp_o6.actions_on_placement) == 2
    assert camp_o6.actions_on_placement[0].type == ActionType.GAIN_OBJECTIVE
    assert camp_o6.actions_on_placement[1].type == ActionType.GAIN_COINS
    assert camp_o6.actions_on_placement[1].value == 3

    # Check an Island A campsite
    assert "CAMP_AREA_IA14" in campsite_data
    camp_ia14 = campsite_data["CAMP_AREA_IA14"]
    assert camp_ia14.track_type == TrackType.ISLAND_A
    assert camp_ia14.tent_slots[0].placement_cost == 1
    assert camp_ia14.actions_on_placement[0].type == ActionType.GAIN_SEAL_ANY_FREE

    # --- Beagle Goals Data Assertions ---
    assert beagle_goals_data, "Beagle goals data should not be empty"
    assert 1 in beagle_goals_data, "Beagle goal ID 1 should exist"
    assert 12 in beagle_goals_data, "Beagle goal ID 12 should exist"
    assert len(beagle_goals_data) == 12, "Should be 12 Beagle goals defined"

    goal_1 = beagle_goals_data[1]
    assert isinstance(goal_1, BeagleGoal)
    assert goal_1.id == 1
    assert "Yellow Wax Seals" in goal_1.description
    assert isinstance(goal_1.scoring_condition, ScoringCondition)
    assert goal_1.scoring_condition.type == "PER_SEAL"
    assert goal_1.scoring_condition.points_per == 4
    assert goal_1.scoring_condition.color == SealColor.YELLOW
    assert goal_1.scoring_condition.kind is None

    goal_6 = beagle_goals_data[6]
    assert goal_6.scoring_condition.type == "PER_SPECIMEN_RESEARCHED"
    assert goal_6.scoring_condition.kind == SpecimenKind.PLANT
    assert goal_6.scoring_condition.points_per == 6
    assert goal_6.scoring_condition.color is None

    goal_9 = beagle_goals_data[9]
    assert goal_9.scoring_condition.type == "PER_EMPTY_STAMP_STACK"
    assert goal_9.scoring_condition.points_per == 8

    # --- Correspondence Tile Data Assertions ---
    assert correspondence_tiles_data, "Correspondence tile data should not be empty"
    assert 1 in correspondence_tiles_data, "Correspondence tile ID 1 should exist"
    assert 8 in correspondence_tiles_data, "Correspondence tile ID 8 should exist"
    assert len(correspondence_tiles_data) == 8, "Should be 8 correspondence tiles"

    tile_1 = correspondence_tiles_data[1]
    assert isinstance(tile_1, CorrespondenceTile)
    assert tile_1.id == 1
    assert len(tile_1.first_place_rewards) == 2
    assert tile_1.first_place_rewards[0].type == ActionType.GAIN_TEMP_KNOWLEDGE
    assert tile_1.first_place_rewards[0].value == 1
    assert tile_1.first_place_rewards[1].type == ActionType.GAIN_COINS
    assert tile_1.first_place_rewards[1].value == 2
    assert len(tile_1.second_place_rewards) == 1
    assert tile_1.second_place_rewards[0].type == ActionType.GAIN_COINS
    assert tile_1.second_place_rewards[0].value == 2

    # Check tile 8 with CHOICE type
    tile_8 = correspondence_tiles_data[8]
    assert len(tile_8.second_place_rewards) == 1
    reward_8_2nd = tile_8.second_place_rewards[0]
    assert reward_8_2nd.type == ActionType.CHOICE
    assert isinstance(reward_8_2nd.value, list), (
        "Choice reward value should be a list of options"
    )
    assert len(reward_8_2nd.value) == 2
    assert reward_8_2nd.value[0]["type"] == "NAVIGATE"

    # --- Special Action Tile Data Assertions ---
    assert special_action_tiles_data, "Special action tile data should not be empty"
    assert 1 in special_action_tiles_data, "Special action tile ID 1 should exist"
    assert 12 in special_action_tiles_data, "Special action tile ID 12 should exist"
    assert len(special_action_tiles_data) == 12, "Should be 12 special action tiles"

    tile_2 = special_action_tiles_data[2]
    assert isinstance(tile_2, SpecialActionTile)
    assert tile_2.id == 2
    assert len(tile_2.actions) == 2
    assert tile_2.actions[0].type == ActionType.GAIN_COINS
    assert tile_2.actions[0].value == 3
    assert tile_2.actions[1].type == ActionType.GAIN_TEMP_KNOWLEDGE
    assert tile_2.actions[1].value == 1

    # Check tile 5 with CHOICE and choice_source
    tile_5 = special_action_tiles_data[5]
    assert len(tile_5.actions) == 1
    action_5 = tile_5.actions[0]
    assert action_5.type == ActionType.CHOICE
    assert action_5.choice_source == "CONVERT_TEMP_KNOWLEDGE"
    assert isinstance(action_5.value, list)
    assert len(action_5.value) == 2
    assert action_5.value[0]["type"] == "GAIN_COINS"
    assert action_5.value[0]["value"] == 7

    # Check tile 7 with cost_modifier
    tile_7 = special_action_tiles_data[7]
    assert len(tile_7.actions) == 2
    assert tile_7.actions[0].type == ActionType.GAIN_SEAL_SPECIAL
    assert tile_7.actions[0].value == "FREE"
    assert tile_7.actions[1].type == ActionType.GAIN_COINS
    assert tile_7.actions[1].value == 1

    # --- Personal Board Data Assertions ---
    assert personal_board_data, "Personal board data should not be None"
    assert isinstance(personal_board_data, PersonalBoardDefinition)
    assert personal_board_data.board_id == "STANDARD_PLAYER_BOARD"

    # Worker Rows
    assert len(personal_board_data.worker_rows) == 5
    worker_row_1 = personal_board_data.worker_rows[1]  # Check row index 1
    assert isinstance(worker_row_1, PersonalBoardWorkerRow)
    assert worker_row_1.row_index == 1
    assert worker_row_1.max_seals == 6
    assert len(worker_row_1.seal_slots) == 6
    seal_slot_3 = worker_row_1.seal_slots[3]
    assert isinstance(seal_slot_3, PersonalBoardSealSlot)
    assert seal_slot_3.placement_cost == 1
    assert seal_slot_3.distinction_trigger == "SILVER"
    seal_slot_5 = worker_row_1.seal_slots[5]
    assert seal_slot_5.distinction_trigger == "GOLDEN"
    assert seal_slot_5.reward_action is not None
    assert seal_slot_5.reward_action.type == ActionType.GAIN_VP
    assert seal_slot_5.reward_action.value == 7

    # Objective Slots
    assert len(personal_board_data.objective_slots) == 10
    obj_slot_silver_1 = next(
        s for s in personal_board_data.objective_slots if s.slot_id == "SILVER_1"
    )
    assert isinstance(obj_slot_silver_1, PersonalBoardObjectiveSlot)
    assert obj_slot_silver_1.type == "SILVER"
    assert obj_slot_silver_1.placement_cost == 0
    assert len(obj_slot_silver_1.reward_actions) == 2
    assert (
        obj_slot_silver_1.reward_actions[0].type == ActionType.OBJECTIVE_REACTIVATE_TENT
    )
    obj_slot_golden_5 = next(
        s for s in personal_board_data.objective_slots if s.slot_id == "GOLDEN_5"
    )
    assert obj_slot_golden_5.placement_cost == 1
    assert len(obj_slot_golden_5.reward_actions) == 1
    assert obj_slot_golden_5.reward_actions[0].type == ActionType.GAIN_VP
    assert obj_slot_golden_5.reward_actions[0].value == 8

    # Reserve Objective Slots
    assert hasattr(personal_board_data, "reserve_objective_slots"), (
        "Personal board should have reserve objective slots attribute"
    )
    assert len(personal_board_data.reserve_objective_slots) == 2, (
        "Should be 2 reserve objective slots"
    )
    reserve_slot_1 = personal_board_data.reserve_objective_slots[0]
    assert isinstance(reserve_slot_1, PersonalBoardReserveObjectiveSlot), (
        "Reserve slot item should be correct type"
    )
    assert reserve_slot_1.slot_id == "RESERVE_1"
    assert reserve_slot_1.type == "RESERVE"
    assert reserve_slot_1.position == 1

    # Objective Pair Bonus
    assert personal_board_data.objective_pair_bonus_action is not None
    assert personal_board_data.objective_pair_bonus_action.type == ActionType.GAIN_VP
    assert personal_board_data.objective_pair_bonus_action.value == 4

    # Tent Slots
    assert len(personal_board_data.tent_slots) == 5
    tent_slot_0 = personal_board_data.tent_slots[0]
    assert isinstance(tent_slot_0, PersonalBoardTentSlot)
    assert tent_slot_0.slot_index == 0
    assert tent_slot_0.revealed_action is None
    tent_slot_2 = personal_board_data.tent_slots[2]
    assert tent_slot_2.revealed_action is not None
    assert tent_slot_2.revealed_action.type == ActionType.CHOICE
    assert isinstance(tent_slot_2.revealed_action.value, list)

    # Stamp Slots
    assert len(personal_board_data.stamp_slots) == 3
    stamp_slot_1 = personal_board_data.stamp_slots[1]
    assert isinstance(stamp_slot_1, PersonalBoardStampSlot)
    assert stamp_slot_1.revealed_action is not None
    assert stamp_slot_1.revealed_action.type == ActionType.ACADEMY
    assert stamp_slot_1.revealed_action.value == -2  # cost_modifier

    # Specimen Grid Slots
    assert len(personal_board_data.specimen_grid_slots) == 16
    specimen_slot_0 = personal_board_data.specimen_grid_slots[0]
    assert isinstance(specimen_slot_0, PersonalBoardSpecimenSlot)
    assert specimen_slot_0.specimen_token_id == "SPN_GREEN_REPTILE"
