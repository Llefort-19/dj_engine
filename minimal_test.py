# minimal_test.py
from dataclasses import dataclass, field
from typing import Any


# Simplified ActionType for testing
# Using a simple class as a placeholder for the actual Enum
class ActionType:
    pass


@dataclass
class SimpleActionInfo:
    type: ActionType
    value: Any = None
    choice_source: str | None = None


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


# Add a basic instantiation to ensure mypy checks usage
ts = TrackSpace(id="test_id")
si = SimpleActionInfo(type=ActionType())
ts.actions.append(si)

print("Minimal test file created. Run 'mypy minimal_test.py'")
