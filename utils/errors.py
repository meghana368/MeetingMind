"""Application-specific exceptions. Messages are safe to show to end users."""


class MeetingMindError(Exception):
    """Base class for errors whose message can be shown in the UI."""


class InputValidationError(MeetingMindError):
    """The user submitted missing or invalid input."""


class HindsightError(MeetingMindError):
    """A Hindsight memory operation failed."""


class LLMError(MeetingMindError):
    """The Groq LLM call failed or returned unusable output."""


class AgentError(MeetingMindError):
    """The agent could not complete a workflow."""
