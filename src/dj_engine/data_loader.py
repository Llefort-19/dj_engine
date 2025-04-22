"""Loads and provides access to static game data from JSON files."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Configure logging
logger = logging.getLogger(__name__)

# --- Dataclasses ---


@dataclass
class BaseData:
    id: str  # Assuming most data items have an ID


@dataclass
class SimpleActionInfo:
    """Represents a simple action definition, often used in rewards/bonuses."""

    type: str  # Consider ActionType Enum later
    # Updated to allow list for CHOICE options
    value: int | str | list[dict[str, Any]] | None = None
    choice_source: str | None = None  # Added for special action tile 5


@dataclass
class AcademyScroll(BaseData):
    # Placeholder fields - inspect academy_scrolls.json
    scroll_row: int  # Using row as the primary identifier conceptually
    cost: int
    slots: int


@dataclass
class ScoringCondition:
    """Defines the condition and points for scoring a Beagle Goal."""

    type: str  # e.g., PER_SEAL, PER_SPECIMEN_RESEARCHED
    points_per: int
    # Optional fields based on type
    color: str | None = None  # TODO: Use SealColor Enum?
    kind: str | None = None  # TODO: Use SpecimenKind Enum?


@dataclass
class BeagleGoal:
    id: int  # goal_id
    description: str
    scoring_condition: ScoringCondition
    # vp: int = 0 # Removed, VP is determined by scoring_condition


@dataclass
class TentSlotInfo:
    """Defines the cost for a specific tent slot at a campsite."""

    slot_index: int
    placement_cost: int


@dataclass
class Campsite(BaseData):
    id: str  # campsite_area_id
    originating_track_space_id: str
    track_type: str  # Potential Enum later
    tent_slots: list[TentSlotInfo]
    actions_on_placement: list[SimpleActionInfo]
    # island: str = "" # Removed, track_type is more informative
    # area_id: str = "" # Removed, using id


@dataclass
class CorrespondenceTile:
    id: int  # tile_id
    first_place_rewards: list[SimpleActionInfo]
    second_place_rewards: list[SimpleActionInfo]
    # stamp_slots: int = 0 # Removed placeholder


@dataclass
class DistinctionBonus:
    """Represents a bonus granted by a silver or golden worker."""

    type: str  # e.g., BONUS_EXPLORE, BONUS_MOVEMENT_STOP
    value: int | None = None  # For bonuses like +1 explore, discount value


@dataclass
class CrewCard:
    id: int
    starting_seal_color: str  # TODO: Consider SealColor Enum
    activation_requirement: dict[str, int]  # Maps seal color to count
    achieved_actions: list[SimpleActionInfo]
    # name: str = ""  # No name field observed in JSON
    # ability: str = "" # Represented by achieved_actions


@dataclass
class TrackSpace(BaseData):
    id: str
    silver_banner: bool = False
    beagle_goal: bool = False
    actions: list[SimpleActionInfo] = field(default_factory=list)
    has_specimen: bool = False
    next: list[str] = field(default_factory=list)
    spawns_explorer_on_island: str | None = None
    campsite_area_id: str | None = None
    golden_ribbon_vp: int | None = None  # VP gained by FIRST player entering


@dataclass
class BoardActionLocation(BaseData):
    id: str  # location_id
    action_type: str  # Consider Enum later
    diary_type: str  # MAIN, SMALL, OTHER, SPECIAL
    placement_type: str  # CIRCULAR_MAGNIFYING_GLASS, SQUARE_MAGNIFYING_GLASS
    locked: bool = False
    unlock_cost: int | None = None
    wax_seal_requirements: dict[str, int] = field(
        default_factory=dict
    )  # Color -> Count
    base_actions: list[SimpleActionInfo] = field(default_factory=list)
    # "silver"/"golden" -> list of bonuses
    distinction_bonuses: dict[str, list[DistinctionBonus]] = field(default_factory=dict)
    # base_cost: dict[str, int] = field(default_factory=dict) # Replaced by base_actions
    # distinction_bonus: dict[str, Any] | None = None # Replaced by distinction_bonuses


@dataclass
class ObjectiveDisplayComponent:
    """Represents component within objective display area (deck or display slot)."""

    component_type: str  # e.g., "DECK_SLOT", "DISPLAY_SLOT"
    objective_type: str  # e.g., "silver", "gold"
    description: str
    count: int | None = None  # Only present for DISPLAY_SLOT


@dataclass
class ObjectiveDisplayAreaInfo:
    """Represents the entire objective display area structure."""

    area_id: str
    description: str
    components: list[ObjectiveDisplayComponent]
    is_worker_placement_location: bool
    # actions_on_placement: List[Any] # Ignoring for now unless needed


@dataclass
class ObjectiveRequirement:
    """Represents a single requirement for an objective tile."""

    type: str  # e.g., HAVE_SEALS, HAVE_SPECIMEN_RESEARCHED
    # Optional fields depending on requirement type
    color: str | None = None  # TODO: Use SealColor Enum?
    kind: str | None = None  # TODO: Use SpecimenKind Enum? Or Color string?
    count: int | None = None
    value: int | None = None  # e.g., for track positions


@dataclass
class ObjectiveTile:
    id: int
    type: str  # "silver", "gold", or "starting" (from starting_objectives_tiles.json)
    requirements: list[ObjectiveRequirement]
    # condition: str = "" # Replaced by requirements list
    # vp: int = 0 # VP seems implicit based on type/game rules, not stored here


@dataclass
class PersonalBoardSealSlot:
    """Defines a single seal slot on a worker row."""

    slot_index: int
    placement_cost: int
    distinction_trigger: str | None = None  # "SILVER" or "GOLDEN"
    # Note: Action timing is in JSON but maybe handled by logic
    reward_action: SimpleActionInfo | None = None


@dataclass
class PersonalBoardWorkerRow:
    """Defines a row on the personal board for a worker."""

    row_index: int
    max_seals: int
    has_starting_special_seal: bool = False
    seal_slots: list[PersonalBoardSealSlot] = field(default_factory=list)


@dataclass
class PersonalBoardObjectiveSlot:
    """Defines a slot for placing objective tiles."""

    slot_id: str  # e.g., SILVER_1, GOLDEN_5
    type: str  # "SILVER" or "GOLDEN"
    position: int  # 1-5
    placement_cost: int
    reward_actions: list[SimpleActionInfo]  # Can have multiple rewards


@dataclass
class PersonalBoardTentSlot:
    """Defines a slot uncovered by placing tents."""

    slot_index: int
    revealed_action: SimpleActionInfo | None = None


@dataclass
class PersonalBoardStampSlot:
    """Defines a slot uncovered by emptying stamp stacks."""

    slot_index: int
    revealed_action: SimpleActionInfo | None = None


@dataclass
class PersonalBoardSpecimenSlot:
    """Defines a slot on the specimen research grid."""

    specimen_token_id: str


@dataclass
class PersonalBoardReserveObjectiveSlot:
    """Defines a slot for reserving objective tiles."""

    slot_id: str
    type: str  # "RESERVE"
    position: int
    # placement_cost seems to be 0, maybe not needed in dataclass?


@dataclass
class PersonalBoardDefinition:
    """Represents the entire static definition of a player's personal board."""

    board_id: str
    worker_rows: list[PersonalBoardWorkerRow]
    objective_slots: list[PersonalBoardObjectiveSlot]
    reserve_objective_slots: list[PersonalBoardReserveObjectiveSlot]  # Added
    tent_slots: list[PersonalBoardTentSlot]
    stamp_slots: list[PersonalBoardStampSlot]
    specimen_grid_slots: list[PersonalBoardSpecimenSlot]
    # Action for filling 5th silver/gold
    objective_pair_bonus_action: SimpleActionInfo | None = None


@dataclass
class SpecialActionTile:
    id: int  # tile_id
    actions: list[SimpleActionInfo]
    # requirements: Dict[str, Any] = field(default_factory=dict)
    # Ignoring empty requirements for now
    # action_details: dict[str, Any] = field(default_factory=dict)
    # Replaced by actions list


@dataclass
class Species(BaseData):
    # Placeholder fields - inspect species.json
    id: str  # Overriding BaseData id to match 'token_id'
    museum_row: str
    museum_col: int
    kind: str  # TODO: Consider using SpecimenKind Enum from constants.py later
    colour: str  # TODO: Consider using Color Enum from constants.py later


@dataclass
class TheoryTrackSpace:
    id: int  # Represents the Theory Points level reached (space_id from JSON)
    book_multiplier: int  # Multiplier for Museum sets awarded at this level
    # vp_reward: int = 0 # VP is calculated based on multiplier and museum at end game
    # level: int = 0 # Replaced by id/space_id
    # effect: str | None = None # No immediate effect listed


# --- Data Loading Functions (Placeholders) ---

DATA_PATH = Path(__file__).parent.parent.parent / "data"


def _load_json(filename: str) -> Any:
    """Helper function to load a JSON file from the data directory."""
    filepath = DATA_PATH / filename
    if not filepath.exists():
        logger.error(f"Data file not found: {filepath}")
        raise FileNotFoundError(f"Data file not found: {filepath}")
    try:
        with open(filepath, encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON from {filepath}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading file {filepath}: {e}")
        raise


def _parse_track_spaces(raw_data: Any, track_name: str) -> dict[str, TrackSpace]:
    """Helper function to parse a list of track space dictionaries."""
    track_data: dict[str, TrackSpace] = {}
    if not isinstance(raw_data, list):
        logger.error(f"{track_name} data is not a list")
        raise TypeError(f"Expected list in {track_name} JSON data")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in {track_name}: {item}")
            continue
        try:
            space_id = item["id"]
            raw_actions = item.get("actions", [])
            parsed_actions: list[SimpleActionInfo] = []
            if isinstance(raw_actions, list):
                for act_item in raw_actions:
                    if isinstance(act_item, dict):
                        action_info = SimpleActionInfo(
                            type=act_item["type"],
                            # Assuming value only for track actions
                            value=act_item.get("value"),
                        )
                        parsed_actions.append(action_info)
                    else:
                        logger.warning(
                            f"Skipping non-dict action in {track_name} "
                            f"space {space_id}: {act_item}"
                        )
            else:
                logger.warning(
                    f"'actions' is not a list in {track_name} "
                    f"space {space_id}: {raw_actions}"
                )

            space = TrackSpace(
                id=space_id,
                silver_banner=item.get("silver_banner", False),
                beagle_goal=item.get("beagle_goal", False),
                actions=parsed_actions,
                has_specimen=item.get("has_specimen", False),
                next=item.get("next", []),
                spawns_explorer_on_island=item.get("spawns_explorer_on_island"),
                campsite_area_id=item.get("campsite_area_id"),
                golden_ribbon_vp=item.get("golden_ribbon_vp"),
            )
            track_data[space_id] = space
        except KeyError as e:
            logger.error(f"Missing key {e} in {track_name} space item: {item}")
        except Exception as e:
            logger.error(f"Error parsing {track_name} space item {item}: {e}")

    logger.info(f"Parsed {len(track_data)} track spaces from {track_name}.")
    return track_data


# Example loading functions (will need implementation and parsing logic)
def load_academy_scrolls() -> dict[int, AcademyScroll]:
    raw_data = _load_json("academy_scrolls.json")
    academy_data: dict[int, AcademyScroll] = {}
    if not isinstance(raw_data, list):
        logger.error("academy_scrolls.json top level is not a list")
        raise TypeError("Expected list in academy_scrolls.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in academy_scrolls.json: {item}")
            continue
        try:
            scroll_row = item["scroll_row"]
            # We pass a dummy 'id' to BaseData, the real key is scroll_row
            scroll = AcademyScroll(
                id=f"scroll_{scroll_row}",  # Create a string ID if BaseData needs one
                scroll_row=scroll_row,
                cost=item["cost"],
                slots=item["slots"],
            )
            academy_data[scroll_row] = scroll
        except KeyError as e:
            logger.error(f"Missing key {e} in academy scroll item: {item}")
        except Exception as e:
            logger.error(f"Error parsing academy scroll item {item}: {e}")

    logger.info(
        f"Parsed {len(academy_data)} academy scrolls from academy_scrolls.json."
    )
    return academy_data


def load_beagles_goals() -> dict[int, BeagleGoal]:
    """Loads Beagle Goal tile definitions."""
    raw_data = _load_json("beagles_goals.json")
    goal_data: dict[int, BeagleGoal] = {}
    if not isinstance(raw_data, list):
        logger.error("beagles_goals.json top level is not a list")
        raise TypeError("Expected list in beagles_goals.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in beagles_goals.json: {item}")
            continue
        try:
            goal_id = item["goal_id"]
            raw_condition = item.get("scoring_condition")

            if not isinstance(raw_condition, dict):
                logger.error(
                    f"Invalid scoring_condition for goal {goal_id}: {raw_condition}"
                )
                continue  # Skip this goal if condition is invalid

            condition = ScoringCondition(
                type=raw_condition["type"],
                points_per=raw_condition["points_per"],
                color=raw_condition.get("color"),
                kind=raw_condition.get("kind"),
            )

            goal = BeagleGoal(
                id=goal_id,
                description=item.get("description", ""),
                scoring_condition=condition,
            )
            goal_data[goal_id] = goal
        except KeyError as e:
            logger.error(f"Missing key {e} in Beagle goal item: {item}")
        except Exception as e:
            logger.error(f"Error parsing Beagle goal item {item}: {e}")

    logger.info(f"Parsed {len(goal_data)} Beagle goals from beagles_goals.json.")
    return goal_data


def load_campsites() -> dict[str, Campsite]:
    """Loads campsite area definitions."""
    raw_data = _load_json("campsites.json")
    campsite_data: dict[str, Campsite] = {}
    if not isinstance(raw_data, list):
        logger.error("campsites.json top level is not a list")
        raise TypeError("Expected list in campsites.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in campsites.json: {item}")
            continue
        try:
            campsite_id = item["campsite_area_id"]

            # Parse tent slots
            raw_slots = item.get("tent_slots", [])
            parsed_slots: list[TentSlotInfo] = []
            if isinstance(raw_slots, list):
                for slot_item in raw_slots:
                    if isinstance(slot_item, dict):
                        slot = TentSlotInfo(
                            slot_index=slot_item["slot_index"],
                            placement_cost=slot_item["placement_cost"],
                        )
                        parsed_slots.append(slot)
            else:
                logger.warning(f"'tent_slots' not a list in campsite {campsite_id}")

            # Parse actions on placement
            raw_actions = item.get("actions_on_placement", [])
            parsed_actions: list[SimpleActionInfo] = []
            if isinstance(raw_actions, list):
                for act_item in raw_actions:
                    if isinstance(act_item, dict):
                        action_info = SimpleActionInfo(
                            type=act_item["type"], value=act_item.get("value")
                        )
                        parsed_actions.append(action_info)
            else:
                logger.warning(
                    f"'actions_on_placement' not a list in campsite {campsite_id}"
                )

            campsite = Campsite(
                id=campsite_id,
                originating_track_space_id=item["originating_track_space_id"],
                track_type=item["track_type"],
                tent_slots=parsed_slots,
                actions_on_placement=parsed_actions,
            )
            campsite_data[campsite_id] = campsite
        except KeyError as e:
            logger.error(f"Missing key {e} in campsite item: {item}")
        except Exception as e:
            logger.error(f"Error parsing campsite item {item}: {e}")

    logger.info(f"Parsed {len(campsite_data)} campsites from campsites.json.")
    return campsite_data


def load_correspondences_tiles() -> dict[int, CorrespondenceTile]:
    """Loads correspondence tile definitions."""
    raw_data = _load_json("correspondances_tiles.json")  # Note spelling
    tile_data: dict[int, CorrespondenceTile] = {}
    if not isinstance(raw_data, list):
        logger.error("correspondances_tiles.json top level is not a list")
        raise TypeError("Expected list in correspondances_tiles.json")

    def _parse_rewards(
        reward_list_raw: Any, tile_id: int, place: str
    ) -> list[SimpleActionInfo]:
        """Helper to parse reward lists (first or second place)."""
        parsed_rewards: list[SimpleActionInfo] = []
        if isinstance(reward_list_raw, list):
            for act_item in reward_list_raw:
                if isinstance(act_item, dict):
                    # Handle the CHOICE type - store its options raw for now
                    # The action logic will need to interpret this later.
                    if act_item.get("type") == "CHOICE":
                        # Storing options dict directly in value for simplicity now.
                        # Might need a more structured approach later
                        # (e.g., separate ChoiceActionInfo)
                        action_info = SimpleActionInfo(
                            type="CHOICE", value=act_item.get("options")
                        )
                    else:
                        action_info = SimpleActionInfo(
                            type=act_item["type"],
                            value=act_item.get("value", act_item.get("cost_modifier")),
                        )
                    parsed_rewards.append(action_info)
                else:
                    logger.warning(
                        f"Skipping non-dict {place} "
                        f"reward in tile {tile_id}: {act_item}"
                    )
        else:
            logger.warning(f"'{place}_place_rewards' not a list in tile {tile_id}")
        return parsed_rewards

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(
                f"Skipping non-dict item in correspondances_tiles.json: {item}"
            )
            continue
        try:
            tile_id = item["tile_id"]
            first_rewards = _parse_rewards(
                item.get("first_place_rewards", []), tile_id, "first"
            )
            second_rewards = _parse_rewards(
                item.get("second_place_rewards", []), tile_id, "second"
            )

            tile = CorrespondenceTile(
                id=tile_id,
                first_place_rewards=first_rewards,
                second_place_rewards=second_rewards,
            )
            tile_data[tile_id] = tile
        except KeyError as e:
            logger.error(f"Missing key {e} in correspondence tile item: {item}")
        except Exception as e:
            logger.error(f"Error parsing correspondence tile item {item}: {e}")

    logger.info(
        f"Parsed {len(tile_data)} correspondence tiles from correspondances_tiles.json."
    )
    return tile_data


def load_crew_cards() -> dict[int, CrewCard]:
    """Loads crew card definitions."""
    raw_data = _load_json("crew_cards.json")
    crew_data: dict[int, CrewCard] = {}
    if not isinstance(raw_data, list):
        logger.error("crew_cards.json top level is not a list")
        raise TypeError("Expected list in crew_cards.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in crew_cards.json: {item}")
            continue
        try:
            card_id = item["card_id"]
            raw_actions = item.get("achieved_actions", [])
            parsed_actions: list[SimpleActionInfo] = []
            if isinstance(raw_actions, list):
                for act_item in raw_actions:
                    if isinstance(act_item, dict):
                        action_info = SimpleActionInfo(
                            type=act_item["type"],
                            # Handle value or modifier
                            value=act_item.get("value", act_item.get("cost_modifier")),
                        )
                        parsed_actions.append(action_info)
                    else:
                        logger.warning(
                            f"Skipping non-dict action "
                            f"in crew card {card_id}: {act_item}"
                        )
            else:
                logger.warning(
                    f"'achieved_actions' is not a list in crew card "
                    f"{card_id}: {raw_actions}"
                )

            card = CrewCard(
                id=card_id,
                starting_seal_color=item["starting_seal_color"],
                activation_requirement=item["activation_requirement"],
                achieved_actions=parsed_actions,
            )
            crew_data[card_id] = card
        except KeyError as e:
            logger.error(f"Missing key {e} in crew card item: {item}")
        except Exception as e:
            logger.error(f"Error parsing crew card item {item}: {e}")

    logger.info(f"Parsed {len(crew_data)} crew cards from crew_cards.json.")
    return crew_data


def load_island_track(island_id: str) -> dict[str, TrackSpace]:
    """Loads track data for a specific island (A, B, or C)."""
    filename = f"island_{island_id.upper()}_tracks.json"
    raw_data = _load_json(filename)
    track_name = f"Island {island_id.upper()} Track"
    return _parse_track_spaces(raw_data, track_name)


def load_main_board_actions() -> dict[str, BoardActionLocation]:
    """Loads main board action location definitions."""
    raw_data = _load_json("main_board_actions.json")
    action_location_data: dict[str, BoardActionLocation] = {}

    for item in raw_data:
        if not isinstance(item, dict):
            # Allow for comments in the JSON list
            if isinstance(item, dict) and "_comment" in item:
                continue
            logger.warning(
                f"Skipping non-dict or non-comment item in "
                f"main_board_actions.json: {item}"
            )
            continue
        # Skip if it's just a comment entry
        if "location_id" not in item:
            continue

        try:
            location_id = item["location_id"]

            # Parse base actions
            raw_base_actions = item.get("base_actions", [])
            parsed_base_actions: list[SimpleActionInfo] = []
            if isinstance(raw_base_actions, list):
                for act_item in raw_base_actions:
                    if isinstance(act_item, dict):
                        action_info = SimpleActionInfo(
                            type=act_item["type"],
                            # Reuse logic from CrewCard
                            value=act_item.get("value", act_item.get("cost_modifier")),
                        )
                        parsed_base_actions.append(action_info)

            # Parse distinction bonuses
            raw_distinctions = item.get("distinction_bonuses", {})
            parsed_distinctions: dict[str, list[DistinctionBonus]] = {
                "silver": [],
                "golden": [],
            }
            if isinstance(raw_distinctions, dict):
                for bonus_type in ["silver", "golden"]:
                    bonus_list = raw_distinctions.get(bonus_type, [])
                    if isinstance(bonus_list, list):
                        for bonus_item in bonus_list:
                            if isinstance(bonus_item, dict):
                                bonus = DistinctionBonus(
                                    type=bonus_item["type"],
                                    value=bonus_item.get("value"),
                                )
                                parsed_distinctions[bonus_type].append(bonus)

            location = BoardActionLocation(
                id=location_id,
                action_type=item["action_type"],
                diary_type=item["diary_type"],
                placement_type=item["placement_type"],
                locked=item.get("locked", False),
                unlock_cost=item.get("unlock_cost"),
                wax_seal_requirements=item.get("wax_seal_requirements", {}),
                base_actions=parsed_base_actions,
                distinction_bonuses=parsed_distinctions,
            )
            action_location_data[location_id] = location

        except KeyError as e:
            logger.error(f"Missing key {e} in main board action item: {item}")
        except Exception as e:
            logger.error(f"Error parsing main board action item {item}: {e}")

    logger.info(
        f"Parsed {len(action_location_data)} main board actions "
        f"from main_board_actions.json."
    )
    return action_location_data


def load_objective_display_area() -> ObjectiveDisplayAreaInfo:
    """Loads the objective display area definition."""
    raw_data = _load_json("objective_display_area.json")
    if not isinstance(raw_data, dict):
        logger.error("objective_display_area.json is not a dictionary")
        raise TypeError("Expected dict in objective_display_area.json")

    parsed_components: list[ObjectiveDisplayComponent] = []
    raw_components = raw_data.get("components", [])
    if not isinstance(raw_components, list):
        logger.error("'components' field in objective_display_area.json is not a list")
        raise TypeError("Expected list for 'components'")

    for comp_item in raw_components:
        if not isinstance(comp_item, dict):
            logger.warning(f"Skipping non-dict component item: {comp_item}")
            continue
        try:
            component = ObjectiveDisplayComponent(
                component_type=comp_item["component_type"],
                objective_type=comp_item["objective_type"],
                # Use .get for optional fields
                description=comp_item.get("description", ""),
                count=comp_item.get("count"),  # Will be None if not present
            )
            parsed_components.append(component)
        except KeyError as e:
            logger.error(f"Missing key {e} in objective display component: {comp_item}")
        except Exception as e:
            logger.error(f"Error parsing objective display component {comp_item}: {e}")

    try:
        area_info = ObjectiveDisplayAreaInfo(
            area_id=raw_data["area_id"],
            description=raw_data.get("description", ""),
            components=parsed_components,
            is_worker_placement_location=raw_data.get(
                "is_worker_placement_location", False
            ),
        )
    except KeyError as e:
        logger.error(f"Missing key {e} in objective_display_area.json top level")
        raise
    except Exception as e:
        logger.error(f"Error creating ObjectiveDisplayAreaInfo: {e}")
        raise

    logger.info(f"Parsed objective display area info for {area_info.area_id}.")
    return area_info


def load_objective_tiles() -> dict[int, ObjectiveTile]:
    """Loads silver and gold objective tile definitions."""
    raw_data = _load_json("objective_tiles.json")
    objective_data: dict[int, ObjectiveTile] = {}
    if not isinstance(raw_data, list):
        logger.error("objective_tiles.json top level is not a list")
        raise TypeError("Expected list in objective_tiles.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in objective_tiles.json: {item}")
            continue
        try:
            objective_id = item["objective_id"]
            raw_reqs = item.get("requirements", [])
            parsed_reqs: list[ObjectiveRequirement] = []
            if isinstance(raw_reqs, list):
                for req_item in raw_reqs:
                    if isinstance(req_item, dict):
                        req = ObjectiveRequirement(
                            type=req_item["type"],
                            color=req_item.get("color"),
                            kind=req_item.get("kind"),
                            count=req_item.get("count"),
                            value=req_item.get("value"),
                        )
                        parsed_reqs.append(req)
                    else:
                        logger.warning(
                            f"Skipping non-dict requirement in objective "
                            f"{objective_id}: {req_item}"
                        )
            else:
                logger.warning(
                    f"'requirements' is not a list in objective "
                    f"{objective_id}: {raw_reqs}"
                )

            tile = ObjectiveTile(
                id=objective_id, type=item["type"], requirements=parsed_reqs
            )
            objective_data[objective_id] = tile
        except KeyError as e:
            logger.error(f"Missing key {e} in objective tile item: {item}")
        except Exception as e:
            logger.error(f"Error parsing objective tile item {item}: {e}")

    logger.info(
        f"Parsed {len(objective_data)} objective tiles from objective_tiles.json."
    )
    return objective_data


def load_ocean_tracks() -> dict[str, TrackSpace]:
    """Loads ocean track data."""
    raw_data = _load_json("ocean_tracks.json")
    return _parse_track_spaces(raw_data, "Ocean Track")


def load_personal_board() -> PersonalBoardDefinition:
    """Loads the personal board definition."""
    raw_data = _load_json("personal_board.json")
    if not isinstance(raw_data, dict):
        logger.error("personal_board.json is not a dictionary")
        raise TypeError("Expected dict in personal_board.json")

    # --- Helper to parse actions (similar to previous parsers) ---
    def _parse_action(
        action_dict: dict[str, Any] | None, context: str
    ) -> SimpleActionInfo | None:
        if not action_dict or not isinstance(action_dict, dict):
            # Allow empty dicts like in tent_slot 0
            if isinstance(action_dict, dict) and not action_dict:
                return None
            logger.warning(f"Invalid action dict in {context}: {action_dict}")
            return None
        try:
            value_data: int | str | list[dict[str, Any]] | None = None
            if action_dict.get("type") == "CHOICE":
                value_data = action_dict.get("options")
            else:
                value_data = action_dict.get("value", action_dict.get("cost_modifier"))

            # Ignoring timing for now - logic needs to handle it
            return SimpleActionInfo(
                type=action_dict["type"],
                value=value_data,
                choice_source=action_dict.get("choice_source"),
            )
        except KeyError as e:
            logger.error(f"Missing key {e} in action for {context}: {action_dict}")
            return None
        except Exception as e:
            logger.error(f"Error parsing action for {context} {action_dict}: {e}")
            return None

    # --- Parse Worker Rows ---
    parsed_worker_rows: list[PersonalBoardWorkerRow] = []
    for row_item in raw_data.get("worker_rows", []):
        if isinstance(row_item, dict):
            try:
                parsed_seal_slots: list[PersonalBoardSealSlot] = []
                for slot_item in row_item.get("seal_slots", []):
                    if isinstance(slot_item, dict):
                        reward_action = _parse_action(
                            slot_item.get("reward_action"),
                            f"worker row {row_item.get('row_index')} seal slot",
                        )
                        slot = PersonalBoardSealSlot(
                            slot_index=slot_item["slot_index"],
                            placement_cost=slot_item["placement_cost"],
                            distinction_trigger=slot_item.get("distinction_trigger"),
                            reward_action=reward_action,
                        )
                        parsed_seal_slots.append(slot)

                row = PersonalBoardWorkerRow(
                    row_index=row_item["row_index"],
                    max_seals=row_item["max_seals"],
                    has_starting_special_seal=row_item.get(
                        "has_starting_special_seal", False
                    ),
                    seal_slots=parsed_seal_slots,
                )
                parsed_worker_rows.append(row)
            except KeyError as e:
                logger.error(f"Missing key {e} in worker row item: {row_item}")
            except Exception as e:
                logger.error(f"Error parsing worker row item {row_item}: {e}")

    # --- Parse Objective Slots ---
    parsed_objective_slots: list[PersonalBoardObjectiveSlot] = []
    for slot_item in raw_data.get("objective_slots", []):
        # Skip comments
        if isinstance(slot_item, dict) and "slot_id" in slot_item:
            try:
                raw_rewards = slot_item.get("reward_action", [])
                parsed_rewards: list[SimpleActionInfo] = []
                if isinstance(raw_rewards, list):
                    for act_item in raw_rewards:
                        action = _parse_action(
                            act_item, f"objective slot {slot_item.get('slot_id')}"
                        )
                        if action:
                            parsed_rewards.append(action)
                elif isinstance(raw_rewards, dict):  # Handle single dict reward
                    action = _parse_action(
                        raw_rewards, f"objective slot {slot_item.get('slot_id')}"
                    )
                    if action:
                        parsed_rewards.append(action)

                # Use unique name: obj_slot
                obj_slot = PersonalBoardObjectiveSlot(
                    slot_id=slot_item["slot_id"],
                    type=slot_item["type"],
                    position=slot_item["position"],
                    placement_cost=slot_item.get("placement_cost", 0),
                    reward_actions=parsed_rewards,
                )
                parsed_objective_slots.append(obj_slot)
            except KeyError as e:
                logger.error(f"Missing key {e} in objective slot item: {slot_item}")
            except Exception as e:
                logger.error(f"Error parsing objective slot item {slot_item}: {e}")

    # --- Parse Objective Pair Bonus ---
    pair_bonus_action = _parse_action(
        raw_data.get("objective_pair_bonus", {}).get("reward_action"),
        "objective pair bonus",
    )

    # --- Parse Tent Slots ---
    parsed_tent_slots: list[PersonalBoardTentSlot] = []
    for slot_item in raw_data.get("tent_slots", []):
        if isinstance(slot_item, dict):
            try:
                action = _parse_action(
                    slot_item.get("revealed_action"),
                    f"tent slot {slot_item.get('slot_index')}",
                )
                # Use unique name: tent_slot
                tent_slot = PersonalBoardTentSlot(
                    slot_index=slot_item["slot_index"], revealed_action=action
                )
                parsed_tent_slots.append(tent_slot)
            except KeyError as e:
                logger.error(f"Missing key {e} in tent slot item: {slot_item}")
            except Exception as e:
                logger.error(f"Error parsing tent slot item {slot_item}: {e}")

    # --- Parse Stamp Slots ---
    parsed_stamp_slots: list[PersonalBoardStampSlot] = []
    for slot_item in raw_data.get("stamp_slots", []):
        if isinstance(slot_item, dict):
            try:
                action = _parse_action(
                    slot_item.get("revealed_action"),
                    f"stamp slot {slot_item.get('slot_index')}",
                )
                # Use unique name: stamp_slot
                stamp_slot = PersonalBoardStampSlot(
                    slot_index=slot_item["slot_index"], revealed_action=action
                )
                parsed_stamp_slots.append(stamp_slot)
            except KeyError as e:
                logger.error(f"Missing key {e} in stamp slot item: {slot_item}")
            except Exception as e:
                logger.error(f"Error parsing stamp slot item {slot_item}: {e}")

    # --- Parse Specimen Grid Slots ---
    parsed_specimen_slots: list[PersonalBoardSpecimenSlot] = []
    for slot_item in raw_data.get("specimen_grid_slots", []):
        if isinstance(slot_item, dict):
            try:
                # Use unique name: specimen_slot
                specimen_slot = PersonalBoardSpecimenSlot(
                    specimen_token_id=slot_item["specimen_token_id"]
                )
                parsed_specimen_slots.append(specimen_slot)
            except KeyError as e:
                logger.error(f"Missing key {e} in specimen slot item: {slot_item}")
            except Exception as e:
                logger.error(f"Error parsing specimen slot item {slot_item}: {e}")

    # --- Parse Reserve Objective Slots --- Added section
    parsed_reserve_slots: list[PersonalBoardReserveObjectiveSlot] = []
    for slot_item in raw_data.get("reserve_objective_slots", []):
        # Skip comments
        if isinstance(slot_item, dict) and "slot_id" in slot_item:
            try:
                # Use unique name: reserve_slot
                reserve_slot = PersonalBoardReserveObjectiveSlot(
                    slot_id=slot_item["slot_id"],
                    type=slot_item["type"],
                    position=slot_item["position"],
                )
                parsed_reserve_slots.append(reserve_slot)
            except KeyError as e:
                logger.error(
                    f"Missing key {e} in reserve objective slot item: {slot_item}"
                )
            except Exception as e:
                logger.error(
                    f"Error parsing reserve objective slot item {slot_item}: {e}"
                )

    # --- Construct Final Object ---
    try:
        board_definition = PersonalBoardDefinition(
            board_id=raw_data["board_id"],
            worker_rows=parsed_worker_rows,
            objective_slots=parsed_objective_slots,
            reserve_objective_slots=parsed_reserve_slots,
            tent_slots=parsed_tent_slots,
            stamp_slots=parsed_stamp_slots,
            specimen_grid_slots=parsed_specimen_slots,
            objective_pair_bonus_action=pair_bonus_action,
        )
    except KeyError as e:
        logger.error(f"Missing key {e} in personal_board.json top level")
        raise
    except Exception as e:
        logger.error(f"Error creating PersonalBoardDefinition: {e}")
        raise

    logger.info(f"Parsed personal board definition for {board_definition.board_id}.")
    return board_definition


def load_special_action_tiles() -> dict[int, SpecialActionTile]:
    """Loads special action tile definitions."""
    raw_data = _load_json("special_action_tiles.json")
    tile_data: dict[int, SpecialActionTile] = {}
    if not isinstance(raw_data, list):
        logger.error("special_action_tiles.json top level is not a list")
        raise TypeError("Expected list in special_action_tiles.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(
                f"Skipping non-dict item in special_action_tiles.json: {item}"
            )
            continue
        try:
            tile_id = item["tile_id"]
            raw_actions = item.get("actions", [])
            parsed_actions: list[SimpleActionInfo] = []
            if isinstance(raw_actions, list):
                for act_item in raw_actions:
                    if isinstance(act_item, dict):
                        # Handle CHOICE type specifically
                        value_data: int | str | list[dict[str, Any]] | None = None
                        if act_item.get("type") == "CHOICE":
                            value_data = act_item.get("options")
                        else:
                            value_data = act_item.get(
                                "value", act_item.get("cost_modifier")
                            )

                        action_info = SimpleActionInfo(
                            type=act_item["type"],
                            value=value_data,
                            choice_source=act_item.get("choice_source"),
                        )
                        parsed_actions.append(action_info)
                    else:
                        logger.warning(
                            f"Skipping non-dict action in special tile "
                            f"{tile_id}: {act_item}"
                        )
            else:
                logger.warning(
                    f"'actions' is not a list in special tile {tile_id}: {raw_actions}"
                )

            tile = SpecialActionTile(id=tile_id, actions=parsed_actions)
            tile_data[tile_id] = tile
        except KeyError as e:
            logger.error(f"Missing key {e} in special action tile item: {item}")
        except Exception as e:
            logger.error(f"Error parsing special action tile item {item}: {e}")

    logger.info(
        f"Parsed {len(tile_data)} special action tiles from special_action_tiles.json."
    )
    return tile_data


def load_species() -> dict[str, Species]:
    raw_data = _load_json("species.json")
    species_data: dict[str, Species] = {}
    if not isinstance(raw_data, list):
        logger.error("species.json top level is not a list")
        raise TypeError("Expected list in species.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in species.json: {item}")
            continue
        try:
            token_id = item["token_id"]
            species = Species(
                id=token_id,
                museum_row=item["museum_row"],
                museum_col=item["museum_col"],
                kind=item["kind"],
                colour=item["colour"],
            )
            species_data[token_id] = species
        except KeyError as e:
            logger.error(f"Missing key {e} in species item: {item}")
        except Exception as e:
            logger.error(f"Error parsing species item {item}: {e}")

    logger.info(f"Parsed {len(species_data)} species from species.json.")
    return species_data


def load_starting_objectives_tiles() -> dict[int, ObjectiveTile]:
    """Loads starting objective tile definitions."""
    raw_data = _load_json("starting_objectives_tiles.json")
    objective_data: dict[int, ObjectiveTile] = {}
    if not isinstance(raw_data, list):
        logger.error("starting_objectives_tiles.json top level is not a list")
        raise TypeError("Expected list in starting_objectives_tiles.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(
                f"Skipping non-dict item in starting_objectives_tiles.json: {item}"
            )
            continue
        try:
            objective_id = item["objective_id"]
            raw_reqs = item.get("requirements", [])
            parsed_reqs: list[ObjectiveRequirement] = []
            if isinstance(raw_reqs, list):
                for req_item in raw_reqs:
                    if isinstance(req_item, dict):
                        req = ObjectiveRequirement(
                            type=req_item["type"],
                            color=req_item.get("color"),
                            kind=req_item.get("kind"),
                            count=req_item.get("count"),
                            value=req_item.get("value"),
                        )
                        parsed_reqs.append(req)
                    else:
                        logger.warning(
                            f"Skipping non-dict requirement in starting objective "
                            f"{objective_id}: {req_item}"
                        )
            else:
                logger.warning(
                    f"'requirements' is not a list in starting objective "
                    f"{objective_id}: {raw_reqs}"
                )

            # NOTE: We are reusing the ObjectiveTile dataclass.
            # The 'type' field will correctly store "silver" or "gold" as per the JSON.
            tile = ObjectiveTile(
                id=objective_id, type=item["type"], requirements=parsed_reqs
            )
            objective_data[objective_id] = tile
        except KeyError as e:
            logger.error(f"Missing key {e} in starting objective tile item: {item}")
        except Exception as e:
            logger.error(f"Error parsing starting objective tile item {item}: {e}")

    logger.info(
        f"Parsed {len(objective_data)} starting objective tiles "
        f"from starting_objectives_tiles.json."
    )
    return objective_data


def load_theory_of_evolution_track() -> dict[int, TheoryTrackSpace]:
    """Loads the Theory of Evolution track definitions."""
    raw_data = _load_json("theory_of_evolution_track.json")
    track_data: dict[int, TheoryTrackSpace] = {}
    if not isinstance(raw_data, list):
        logger.error("theory_of_evolution_track.json top level is not a list")
        raise TypeError("Expected list in theory_of_evolution_track.json")

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(f"Skipping non-dict item in theory track: {item}")
            continue
        try:
            space_id = item["space_id"]
            space = TheoryTrackSpace(
                id=space_id, book_multiplier=item["book_multiplier"]
            )
            track_data[space_id] = space
        except KeyError as e:
            logger.error(f"Missing key {e} in theory track item: {item}")
        except Exception as e:
            logger.error(f"Error parsing theory track item {item}: {e}")

    logger.info(
        f"Parsed {len(track_data)} theory track spaces "
        f"from theory_of_evolution_track.json."
    )
    return track_data


# --- Module-level Data Storage (Example) ---

# Using module-level variables for now. Could be encapsulated in a class later.
# We will populate these by calling the load functions.

ACADEMY_SCROLLS_DATA: dict[int, AcademyScroll] = {}
BEAGLES_GOALS_DATA: dict[int, BeagleGoal] = {}
CAMPSITES_DATA: dict[str, Campsite] = {}
CORRESPONDENCES_TILES_DATA: dict[int, CorrespondenceTile] = {}
CREW_CARDS_DATA: dict[int, CrewCard] = {}
ISLAND_A_TRACK_DATA: dict[str, TrackSpace] = {}
ISLAND_B_TRACK_DATA: dict[str, TrackSpace] = {}
ISLAND_C_TRACK_DATA: dict[str, TrackSpace] = {}
MAIN_BOARD_ACTIONS_DATA: dict[str, BoardActionLocation] = {}
OBJECTIVE_DISPLAY_AREA_DATA: ObjectiveDisplayAreaInfo | None = None  # Updated type hint
OBJECTIVE_TILES_DATA: dict[int, ObjectiveTile] = {}
OCEAN_TRACK_DATA: dict[str, TrackSpace] = {}
PERSONAL_BOARD_DATA: PersonalBoardDefinition | None = None  # Updated type hint
SPECIAL_ACTION_TILES_DATA: dict[int, SpecialActionTile] = {}
SPECIES_DATA: dict[str, Species] = {}
STARTING_OBJECTIVES_TILES_DATA: dict[int, ObjectiveTile] = {}
THEORY_OF_EVOLUTION_TRACK_DATA: dict[
    int, TheoryTrackSpace
] = {}  # Key by space_id (int)


def load_all_data() -> None:
    """Loads all static game data into module-level variables."""
    global \
        ACADEMY_SCROLLS_DATA, \
        BEAGLES_GOALS_DATA, \
        CAMPSITES_DATA, \
        CORRESPONDENCES_TILES_DATA, \
        CREW_CARDS_DATA, \
        ISLAND_A_TRACK_DATA, \
        ISLAND_B_TRACK_DATA, \
        ISLAND_C_TRACK_DATA, \
        MAIN_BOARD_ACTIONS_DATA, \
        OBJECTIVE_DISPLAY_AREA_DATA, \
        OBJECTIVE_TILES_DATA, \
        OCEAN_TRACK_DATA, \
        PERSONAL_BOARD_DATA, \
        SPECIAL_ACTION_TILES_DATA, \
        SPECIES_DATA, \
        STARTING_OBJECTIVES_TILES_DATA, \
        THEORY_OF_EVOLUTION_TRACK_DATA

    logger.info("Loading all static game data...")

    ACADEMY_SCROLLS_DATA = load_academy_scrolls()
    BEAGLES_GOALS_DATA = load_beagles_goals()
    CAMPSITES_DATA = load_campsites()
    CORRESPONDENCES_TILES_DATA = load_correspondences_tiles()
    CREW_CARDS_DATA = load_crew_cards()
    ISLAND_A_TRACK_DATA = load_island_track("A")
    ISLAND_B_TRACK_DATA = load_island_track("B")
    ISLAND_C_TRACK_DATA = load_island_track("C")
    MAIN_BOARD_ACTIONS_DATA = load_main_board_actions()
    OBJECTIVE_DISPLAY_AREA_DATA = load_objective_display_area()  # Assign directly
    OBJECTIVE_TILES_DATA = load_objective_tiles()
    OCEAN_TRACK_DATA = load_ocean_tracks()
    PERSONAL_BOARD_DATA = load_personal_board()
    SPECIAL_ACTION_TILES_DATA = load_special_action_tiles()
    SPECIES_DATA = load_species()
    STARTING_OBJECTIVES_TILES_DATA = load_starting_objectives_tiles()
    THEORY_OF_EVOLUTION_TRACK_DATA = load_theory_of_evolution_track()

    logger.info("Finished loading all static game data.")


# Optional: Load data automatically when the module is imported
# load_all_data()
# Consider if this is desired, or if loading should be explicitly triggered.
