"""Custom exceptions for the Darwin's Journey game engine."""


class GameError(Exception):
    """Base class for all custom errors in the dj_engine."""

    pass


class InvalidActionError(GameError):
    """Raised when a player attempts an invalid action."""

    pass


class InsufficientResourcesError(InvalidActionError):
    """Raised when an action fails due to insufficient resources"""

    """(coins, knowledge, etc.)."""

    pass


# Add other custom exceptions as needed, e.g.:
# class InvalidLocationError(InvalidActionError):
#     pass
# class InvalidWorkerError(InvalidActionError):
#     pass
