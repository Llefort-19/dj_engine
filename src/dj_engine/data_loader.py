"""Loads and provides access to static game data from JSON files."""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .constants import (
    ActionType,
    ObjectiveRequirementType,
    SealColor,
    SpecimenKind,
    TrackType,
)

# Configure logging
logger = logging.getLogger(__name__)

# --- Dataclasses ---


@dataclass
class SimpleActionInfo:
    """Represents a simple action definition, often used in rewards/bonuses."""

    type: ActionType | str
    # Core value (e.g., amount, VP, count). Use specific fields below for other details.
    value: int | list[dict[str, Any]] | None = None  # Keep list for CHOICE options
    choice_source: str | None = None
    # New optional fields for richer action descriptions
    cost: int | None = None
    location: str | None = None  # e.g., CAMPSITE_ID, "ANY", "START_OF_NEW_ISLAND"
    distributed: bool | None = None  # For CORRESPONDENCE
    repeat: bool | None = None  # For DELIVER_SPECIMEN
    color: SealColor | str | None = None  # For GAIN_SEAL, allows "ANY"


@dataclass
class AcademyScroll:
    id: str
    scroll_row: int
    cost: int
    slots: int


@dataclass
class ScoringCondition:
    """Defines the condition and points for scoring a Beagle Goal."""

    type: str  # e.g., PER_SEAL, PER_SPECIMEN_RESEARCHED
    points_per: int
    # Optional fields based on type
    color: SealColor | None = None
    kind: SpecimenKind | None = None


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
class Campsite:
    id: str
    originating_track_space_id: str
    track_type: TrackType
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


# Uncommenting CrewCard
@dataclass
class CrewCard:
    id: int
    starting_seal_color: SealColor
    activation_requirement: dict[SealColor, int] = field(default_factory=dict)
    achieved_actions: list[SimpleActionInfo] = field(default_factory=list)
    # name: str = ""  # No name field observed in JSON
    # ability: str = "" # Represented by achieved_actions


@dataclass
class TrackSpace:
    id: str
    silver_banner: bool = False
    beagle_goal: bool = False
    actions: list[SimpleActionInfo] = field(default_factory=list)
    has_specimen: bool = False
    next: list[str] = field(default_factory=list)
    spawns_explorer_on_island: str | None = None
    campsite_area_id: str | None = None
    golden_ribbon_vp: int | None = None


@dataclass
class BoardActionLocation:
    id: str
    action_type: str
    diary_type: str  # MAIN, SMALL, OTHER, SPECIAL
    placement_type: str  # CIRCULAR_MAGNIFYING_GLASS, SQUARE_MAGNIFYING_GLASS
    locked: bool = False
    unlock_cost: int | None = None
    wax_seal_requirements: dict[SealColor, int] = field(
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

    type: ObjectiveRequirementType
    # Optional fields depending on requirement type
    color: SealColor | None = None
    kind: SpecimenKind | None = None
    count: int | None = None
    value: int | None = None  # e.g., for track positions


@dataclass
class ObjectiveTile:
    id: int
    type: str  # "silver" or "gold"
    requirements: list[ObjectiveRequirement]
    starting: bool = False  # True if it's a starting objective
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
class Species:
    id: str
    museum_row: str
    museum_col: int
    kind: SpecimenKind
    color: SealColor


@dataclass
class TheoryTrackSpace:
    id: int  # Represents the Theory Points level reached (space_id from JSON)
    book_multiplier: int  # Multiplier for Museum sets awarded at this level
    # vp_reward: int = 0 # VP is calculated based on multiplier and museum at end game
    # level: int = 0 # Replaced by id/space_id
    # effect: str | None = None # No immediate effect listed


# --- Data Loading Functions (Placeholders) ---

# Correct path assuming data/ is at the project root (sibling to src/)
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

            # Restore full instantiation
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


def _parse_action(
    action_dict: dict[str, Any] | None, context: str
) -> SimpleActionInfo | None:
    """Helper function to parse an action dictionary, handling various keys."""
    # Handle None input gracefully
    if action_dict is None:
        return None

    if not isinstance(action_dict, dict) or not action_dict:
        # Allow empty dicts, treat as None
        return None

    try:
        action_type_str = action_dict["type"]
        action_type_val: ActionType | str
        # parsed_info = SimpleActionInfo(type=None)  # Removed initialization here

        # --- Determine Action Type ---
        if action_type_str == "SPECIAL":
            action_type_val = ActionType.PERFORM_SPECIAL_TILE_ACTION
        elif action_type_str.startswith("OBJECTIVE_"):
            action_type_val = action_type_str  # Keep as string
        else:
            try:
                action_type_val = ActionType[action_type_str]  # Convert to Enum
            except KeyError:
                logger.error(
                    f"Invalid action type string '{action_type_str}' "
                    f"in {context}: {action_dict}"
                )
                return None

        # --- Initialize SimpleActionInfo --- Now that type is known
        parsed_info = SimpleActionInfo(type=action_type_val)

        # --- Populate Fields Based on Keys ---

        # 1. Cost (Standardize cost/cost_modifier/cost_delta -> cost field)
        if "cost" in action_dict:
            parsed_info.cost = action_dict.get("cost")
        elif "cost_modifier" in action_dict:
            cost_mod = action_dict.get("cost_modifier")
            parsed_info.cost = 0 if cost_mod == "FREE" else cost_mod
        elif "cost_delta" in action_dict:  # Added check for cost_delta
            parsed_info.cost = action_dict.get("cost_delta")

        # 2. Value (Primary numeric value or CHOICE options)
        if (
            isinstance(action_type_val, ActionType)
            and action_type_val == ActionType.CHOICE
        ):
            parsed_info.value = action_dict.get("options")
        elif "value" in action_dict:
            # ACADEMY cost sometimes stored as negative value (handled by cost logic)
            # Only assign value if it's not implicitly a cost
            if not (
                isinstance(action_type_val, ActionType)
                and action_type_val == ActionType.ACADEMY
                and isinstance(parsed_info.cost, int)
            ):
                parsed_info.value = action_dict.get("value")

        # 3. Location (ESTABLISH_CAMPSITE, PLACE_EXPLORER)
        if isinstance(action_type_val, ActionType) and action_type_val in [
            ActionType.ESTABLISH_CAMPSITE,
            ActionType.PLACE_EXPLORER,
        ]:
            parsed_info.location = action_dict.get("location")

        # 4. Distributed (CORRESPONDENCE)
        if (
            isinstance(action_type_val, ActionType)
            and action_type_val == ActionType.CORRESPONDENCE
        ):
            parsed_info.distributed = action_dict.get("distributed")

        # 5. Repeat (DELIVER_SPECIMEN)
        if (
            isinstance(action_type_val, ActionType)
            and action_type_val == ActionType.DELIVER_SPECIMEN
        ):
            parsed_info.repeat = action_dict.get("repeat")

        # 6. Color (GAIN_SEAL)
        if (
            isinstance(action_type_val, ActionType)
            and action_type_val == ActionType.GAIN_SEAL
        ):
            color_data = action_dict.get("color")
            if color_data == "ANY":
                parsed_info.color = "ANY"
            elif color_data:
                try:
                    parsed_info.color = SealColor[color_data]
                except KeyError:
                    logger.warning(
                        f"Invalid seal color '{color_data}' for GAIN_SEAL in {context}"
                    )
            # Cost for GAIN_SEAL is handled by generic cost logic (step 1)

        # 7. Choice Source (Specific CHOICE actions)
        parsed_info.choice_source = action_dict.get("choice_source")

        # 8. Cleanup for Special Placeholder
        if action_type_val == ActionType.PERFORM_SPECIAL_TILE_ACTION:
            parsed_info.value = None
            parsed_info.cost = None

        # --- End Population ---

        return parsed_info

    except KeyError as e:
        logger.error(f"Missing key {e} in action for {context}: {action_dict}")
        return None
    except Exception as e:
        logger.error(f"Error parsing action for {context} {action_dict}: {e}")
        return None


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

            # Parse scoring condition with Enum conversion
            condition_type_str = raw_condition["type"]
            # TODO: Implement ScoringConditionType Enum?
            # For now, keep type as str, but parse color/kind
            color_str = raw_condition.get("color")
            kind_str = raw_condition.get("kind")

            color_enum: SealColor | None = None
            if color_str:
                try:
                    color_enum = SealColor[color_str]
                except KeyError:
                    logger.warning(
                        f"Invalid scoring condition color '{color_str}' "
                        f"in goal {goal_id}: {raw_condition}"
                    )

            kind_enum: SpecimenKind | None = None
            if kind_str:
                try:
                    kind_enum = SpecimenKind[kind_str]
                except KeyError:
                    logger.warning(
                        f"Invalid scoring condition kind '{kind_str}' "
                        f"in goal {goal_id}: {raw_condition}"
                    )

            condition = ScoringCondition(
                type=condition_type_str,  # Keeping type as str for now
                points_per=raw_condition["points_per"],
                color=color_enum,
                kind=kind_enum,
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
            track_type_str = item["track_type"]

            try:
                # Use value lookup now that Enum values match JSON strings
                track_type_enum = TrackType(track_type_str)
            except ValueError:  # Catch ValueError for invalid value lookup
                logger.error(
                    f"Invalid track type string '{track_type_str}' "
                    f"for campsite {campsite_id}: {item}"
                )
                continue  # Skip this campsite

            # Parse tent slots (no enums here)
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

            # Parse actions on placement (uses _parse_action which handles Enums)
            raw_actions = item.get("actions_on_placement", [])
            parsed_actions: list[SimpleActionInfo] = []
            if isinstance(raw_actions, list):
                for act_item in raw_actions:
                    # Use _parse_action helper
                    action_info = _parse_action(
                        act_item, f"campsite {campsite_id} action"
                    )
                    if action_info:
                        parsed_actions.append(action_info)
            else:
                logger.warning(
                    f"'actions_on_placement' not a list in campsite {campsite_id}"
                )

            campsite = Campsite(
                id=campsite_id,
                originating_track_space_id=item["originating_track_space_id"],
                track_type=track_type_enum,
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
    raw_data = _load_json("correspondence_tiles.json")  # Corrected spelling
    tile_data: dict[int, CorrespondenceTile] = {}
    if not isinstance(raw_data, list):
        logger.error(
            "correspondence_tiles.json top level is not a list"
        )  # Corrected filename in log
        raise TypeError(
            "Expected list in correspondence_tiles.json"
        )  # Corrected filename in error

    def _parse_rewards(
        reward_list_raw: Any, tile_id: int, place: str
    ) -> list[SimpleActionInfo]:
        """Helper to parse reward lists (first or second place)."""
        parsed_rewards: list[SimpleActionInfo] = []
        if isinstance(reward_list_raw, list):
            for act_item in reward_list_raw:
                # Reuse the main _parse_action helper which handles Enum conversion
                action_info = _parse_action(
                    act_item, f"correspondence tile {tile_id} {place} reward"
                )
                if action_info:
                    parsed_rewards.append(action_info)
                else:
                    # _parse_action already logs warnings/errors
                    pass
                    # logger.warning(
                    #     f"Skipping non-dict {place} "
                    #     f"reward in tile {tile_id}: {act_item}"
                    # )
        else:
            logger.warning(f"'{place}_place_rewards' not a list in tile {tile_id}")
        return parsed_rewards

    for item in raw_data:
        if not isinstance(item, dict):
            logger.warning(
                f"Skipping non-dict item in correspondence_tiles.json: {item}"
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

    logger.info(f"Parsed {len(tile_data)} tiles from correspondence_tiles.json.")
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
            start_seal_str = item["starting_seal_color"]
            raw_req = item["activation_requirement"]

            try:
                start_seal_enum = SealColor[start_seal_str]
            except KeyError:
                logger.error(
                    f"Invalid starting seal color '{start_seal_str}' "
                    f"for crew card {card_id}: {item}"
                )
                continue  # Skip this card

            # Parse activation requirement dict (keys are SealColor)
            parsed_req: dict[SealColor, int] = {}
            if isinstance(raw_req, dict):
                for seal_str, count in raw_req.items():
                    try:
                        seal_enum = SealColor[seal_str]
                        if isinstance(count, int):
                            parsed_req[seal_enum] = count
                        else:
                            logger.warning(
                                f"Invalid count '{count}' for seal '{seal_str}' "
                                f"in crew card {card_id} requirement"
                            )
                    except KeyError:
                        logger.warning(
                            f"Invalid seal color key '{seal_str}' "
                            f"in crew card {card_id} requirement: {raw_req}"
                        )
            else:
                logger.warning(
                    f"Invalid activation_requirement format for crew card {card_id}"
                )

            # Parse achieved actions (uses _parse_action)
            raw_actions = item.get("achieved_actions", [])
            parsed_actions: list[SimpleActionInfo] = []
            if isinstance(raw_actions, list):
                for act_item in raw_actions:
                    action_info = _parse_action(act_item, f"crew card {card_id} action")
                    if action_info:
                        parsed_actions.append(action_info)
            else:
                logger.warning(
                    f"'achieved_actions' is not a list in crew card "
                    f"{card_id}: {raw_actions}"
                )

            card = CrewCard(
                id=card_id,
                starting_seal_color=start_seal_enum,
                activation_requirement=parsed_req,
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
            action_type_str = item["action_type"]

            # Parse base actions (uses _parse_action)
            raw_base_actions = item.get("base_actions", [])
            parsed_base_actions: list[SimpleActionInfo] = []
            if isinstance(raw_base_actions, list):
                for act_item in raw_base_actions:
                    action_info = _parse_action(
                        act_item, f"location {location_id} base action"
                    )
                    if action_info:
                        parsed_base_actions.append(action_info)

            # Parse wax seal requirements (keys are SealColor)
            raw_wax_req = item.get("wax_seal_requirements", {})
            parsed_wax_req: dict[SealColor, int] = {}
            if isinstance(raw_wax_req, dict):
                for seal_str, count in raw_wax_req.items():
                    try:
                        seal_enum = SealColor[seal_str]
                        if isinstance(count, int):
                            parsed_wax_req[seal_enum] = count
                        else:
                            logger.warning(
                                f"Invalid count '{count}' for seal '{seal_str}' "
                                f"in location {location_id} requirement"
                            )
                    except KeyError:
                        logger.warning(
                            f"Invalid seal color key '{seal_str}' "
                            f"in location {location_id} requirement: {raw_wax_req}"
                        )
            else:
                logger.warning(
                    f"Invalid wax_seal_requirements format for location {location_id}"
                )

            # Parse distinction bonuses (no enums here yet)
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
                                    type=bonus_item["type"],  # Keep type as str for now
                                    value=bonus_item.get("value"),
                                )
                                parsed_distinctions[bonus_type].append(bonus)

            location = BoardActionLocation(
                id=location_id,
                action_type=action_type_str,
                diary_type=item["diary_type"],
                placement_type=item["placement_type"],
                locked=item.get("locked", False),
                unlock_cost=item.get("unlock_cost"),
                wax_seal_requirements=parsed_wax_req,
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
                        req_type_str = req_item.get("type")
                        if not req_type_str:
                            logger.warning(
                                f"Missing req type for start obj {objective_id}"
                            )
                            continue

                        color_str = req_item.get("color")
                        kind_str = req_item.get("kind")
                        color_enum: SealColor | None = None
                        kind_enum: SpecimenKind | None = None

                        try:
                            req_type_enum = ObjectiveRequirementType[req_type_str]
                        except KeyError:
                            logger.error(
                                f"Invalid objective req type '{req_type_str}' "
                                f"in objective {objective_id}: {req_item}"
                            )
                            continue  # Skip this requirement

                        # --- Conditional Parsing based on Type ---
                        if req_type_enum == ObjectiveRequirementType.HAVE_SEALS:
                            if color_str:
                                try:
                                    color_enum = SealColor[color_str]
                                except KeyError:
                                    logger.warning(
                                        f"Invalid color '{color_str}' for HAVE_SEALS "
                                        f"in obj {objective_id}: {req_item}"
                                    )
                            # Kind is not relevant for HAVE_SEALS
                        elif (
                            req_type_enum
                            == ObjectiveRequirementType.HAVE_SPECIMEN_RESEARCHED
                        ):
                            if color_str:
                                try:
                                    # Specimen can have color (e.g. RED)
                                    color_enum = SealColor[color_str]
                                except KeyError:
                                    logger.warning(
                                        f"Invalid color '{color_str}' for SPECIMEN req "
                                        f"in objective {objective_id}: {req_item}"
                                    )
                            if kind_str:
                                try:
                                    kind_enum = SpecimenKind[kind_str]
                                except KeyError:
                                    logger.warning(
                                        f"Invalid kind '{kind_str}' for SPECIMEN req "
                                        f"in objective {objective_id}: {req_item}"
                                    )
                        # Add elif for other types needing color/kind if any arise
                        # --- End Conditional Parsing ---

                        req = ObjectiveRequirement(
                            type=req_type_enum,
                            color=color_enum,  # Will be None if not relevant/parsed
                            kind=kind_enum,  # Will be None if not relevant/parsed
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

            # Type for ObjectiveTile remains str for silver/gold
            tile = ObjectiveTile(
                id=objective_id,
                type=item["type"],
                requirements=parsed_reqs,
                starting=item.get("starting", False),  # Read the new boolean flag
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
                    # Use the central _parse_action helper
                    action_info = _parse_action(act_item, f"special tile {tile_id}")
                    if action_info:
                        parsed_actions.append(action_info)
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
            kind_str = item["kind"]
            color_str = item["color"]

            try:
                kind_enum = SpecimenKind[kind_str]
            except KeyError:
                logger.error(
                    f"Invalid specimen kind string '{kind_str}' "
                    f"for species {token_id}: {item}"
                )
                continue  # Skip this species

            try:
                # Assuming color in JSON maps directly to SealColor enum names
                # (e.g., "BLUE", "GREEN", etc.)
                color_enum = SealColor[color_str]
            except KeyError:
                logger.error(
                    f"Invalid species color string '{color_str}' "
                    f"for species {token_id}: {item}"
                )
                continue  # Skip this species

            species = Species(
                id=token_id,
                museum_row=item["museum_row"],
                museum_col=item["museum_col"],
                kind=kind_enum,
                color=color_enum,
            )
            species_data[token_id] = species
        except KeyError as e:
            logger.error(f"Missing key {e} in species item: {item}")
        except Exception as e:
            logger.error(f"Error parsing species item {item}: {e}")

    logger.info(f"Parsed {len(species_data)} species from species.json.")
    return species_data


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
THEORY_OF_EVOLUTION_TRACK_DATA: dict[
    int, TheoryTrackSpace
] = {}  # Key by space_id (int)


def load_all_data() -> dict[str, Any]:
    """Loads all static game data and returns it in a dictionary."""
    # Remove global declarations as we assign directly and return
    # global \
    #     ACADEMY_SCROLLS_DATA, ...

    logger.info("Loading all static game data...")

    # Load into local variables first
    local_academy_scrolls = load_academy_scrolls()
    local_beagles_goals = load_beagles_goals()
    local_campsites = load_campsites()
    local_correspondences = load_correspondences_tiles()
    local_crew_cards = load_crew_cards()
    local_island_a = load_island_track("A")
    local_island_b = load_island_track("B")
    local_island_c = load_island_track("C")
    local_main_board_actions = load_main_board_actions()
    local_objective_display = load_objective_display_area()
    local_objective_tiles = load_objective_tiles()
    local_ocean_tracks = load_ocean_tracks()
    local_personal_board = load_personal_board()
    local_special_tiles = load_special_action_tiles()
    local_species = load_species()
    local_theory_track = load_theory_of_evolution_track()

    # Assign to module-level globals (for potential compatibility)
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
        THEORY_OF_EVOLUTION_TRACK_DATA

    ACADEMY_SCROLLS_DATA = local_academy_scrolls
    BEAGLES_GOALS_DATA = local_beagles_goals
    CAMPSITES_DATA = local_campsites
    CORRESPONDENCES_TILES_DATA = local_correspondences
    CREW_CARDS_DATA = local_crew_cards
    ISLAND_A_TRACK_DATA = local_island_a
    ISLAND_B_TRACK_DATA = local_island_b
    ISLAND_C_TRACK_DATA = local_island_c
    MAIN_BOARD_ACTIONS_DATA = local_main_board_actions
    OBJECTIVE_DISPLAY_AREA_DATA = local_objective_display
    OBJECTIVE_TILES_DATA = local_objective_tiles
    OCEAN_TRACK_DATA = local_ocean_tracks
    PERSONAL_BOARD_DATA = local_personal_board
    SPECIAL_ACTION_TILES_DATA = local_special_tiles
    SPECIES_DATA = local_species
    THEORY_OF_EVOLUTION_TRACK_DATA = local_theory_track

    # Log counts (using local vars)
    logger.debug(f"Loaded {len(local_academy_scrolls)} academy scrolls.")
    logger.debug(f"Loaded {len(local_beagles_goals)} Beagle goals.")
    logger.debug(f"Loaded {len(local_campsites)} campsites.")
    logger.debug(f"Loaded {len(local_correspondences)} correspondence tiles.")
    logger.debug(f"Loaded {len(local_crew_cards)} crew cards.")
    logger.debug(f"Loaded {len(local_island_a)} Island A track spaces.")
    logger.debug(f"Loaded {len(local_island_b)} Island B track spaces.")
    logger.debug(f"Loaded {len(local_island_c)} Island C track spaces.")
    logger.debug(f"Loaded {len(local_main_board_actions)} main board actions.")
    obj_display_loaded = "Yes" if local_objective_display else "No"
    logger.debug(f"Loaded objective display area: {obj_display_loaded}")
    logger.debug(f"Loaded {len(local_objective_tiles)} objective tiles.")
    logger.debug(f"Loaded {len(local_ocean_tracks)} ocean track spaces.")
    personal_board_loaded = "Yes" if local_personal_board else "No"
    logger.debug(f"Loaded personal board definition: {personal_board_loaded}")
    logger.debug(f"Loaded {len(local_special_tiles)} special action tiles.")
    logger.debug(f"Loaded {len(local_species)} species.")
    logger.debug(f"Loaded {len(local_theory_track)} theory track spaces.")

    logger.info("Finished loading all static game data.")

    # Return dictionary of loaded data
    return {
        "academy_scrolls": local_academy_scrolls,
        "beagles_goals": local_beagles_goals,
        "campsites": local_campsites,
        "correspondences_tiles": local_correspondences,
        "crew_cards": local_crew_cards,
        "island_a_track": local_island_a,
        "island_b_track": local_island_b,
        "island_c_track": local_island_c,
        "main_board_actions": local_main_board_actions,
        "objective_display_area": local_objective_display,
        "objective_tiles": local_objective_tiles,
        "ocean_track": local_ocean_tracks,
        "personal_board": local_personal_board,
        "special_action_tiles": local_special_tiles,
        "species": local_species,
        "theory_track": local_theory_track,
    }


# Optional: Load data automatically when the module is imported
# load_all_data()
