"""Sample data for the Sarah Johnson three-meeting demo scenario."""
from typing import Dict

DEMO_CONTACT = "Sarah Johnson"

DEMO_PREP: Dict[int, Dict[str, str]] = {
    1: {"purpose": "Introductory discovery call about our product", "date": "2026-09-01"},
    2: {"purpose": "Follow-up on implementation and next steps", "date": "2026-09-15"},
    3: {"purpose": "Analytics demo and pricing discussion", "date": "2026-09-29"},
}

DEMO_NOTES: Dict[int, Dict[str, str]] = {
    1: {
        "date": "2026-09-01",
        "title": "Product implementation discovery call",
        "notes": (
            "Call with Sarah Johnson, VP of Operations at Brightwave. Sarah said the "
            "implementation timeline is her biggest concern - her team cannot afford more "
            "than a 6-week rollout. I promised to send her a detailed implementation "
            "proposal by Friday. She prefers short, direct emails with clear dates and "
            "dislikes long slide decks. We agreed to hold a follow-up meeting in two weeks."
        ),
    },
    2: {
        "date": "2026-09-15",
        "title": "Implementation follow-up",
        "notes": (
            "Follow-up with Sarah Johnson. I sent the implementation proposal last Friday "
            "and walked her through the phased rollout plan. Sarah said she is now "
            "comfortable with the implementation timeline and no longer sees it as a risk. "
            "She asked many questions about the analytics features, especially executive "
            "dashboards and exporting data to Excel. Decision: Sarah wants to see an "
            "analytics demo. I promised to book an analytics demo for her team and send "
            "sample dashboards."
        ),
    },
}
