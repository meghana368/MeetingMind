"""Prompt templates for extraction and brief generation."""
from __future__ import annotations

from typing import List

EXTRACTION_SYSTEM_PROMPT = (
    "You extract durable facts from meeting notes for a meeting-preparation agent. "
    "Return ONLY a JSON object with exactly these keys, each a list of short, "
    "self-contained strings: topics, decisions, commitments, concerns, action_items, "
    "preferences, unresolved_issues, outcomes, resolved_issues.\n"
    "Rules:\n"
    "- Refer to people by name. The person who wrote the notes is 'the user'.\n"
    "- commitments: promises made. Start each with who made it, e.g. "
    "'The user promised to send the implementation proposal by Friday'.\n"
    "- concerns: worries or objections the other person raised.\n"
    "- unresolved_issues: things still open after the meeting (e.g. a proposal that still "
    "needs to be sent).\n"
    "- resolved_issues: concerns, problems or earlier commitments that these notes show "
    "are now resolved, fulfilled, or no longer a concern. Be explicit, e.g. "
    "'Sarah's implementation timeline concern is resolved'.\n"
    "- preferences: preferences, interests, communication style, important facts.\n"
    "- Only include what the notes support. Use [] when nothing applies. No markdown."
)


def build_extraction_prompt(contact_name: str, meeting_date: str, title: str, notes: str) -> str:
    return (
        f"Contact: {contact_name}\nMeeting date: {meeting_date}\nMeeting title: {title}\n\n"
        f"Meeting notes:\n{notes}\n\nReturn the JSON object now."
    )


BRIEF_SYSTEM_PROMPT = (
    "You are MeetingMind, an AI meeting-preparation agent with long-term memory. "
    "You receive memories recalled from Hindsight about one contact, then write a "
    "personalised meeting brief.\n"
    "Rules:\n"
    "- Memories start with a [YYYY-MM-DD] date. Later dates supersede earlier ones.\n"
    "- A memory marked RESOLVED / COMPLETED closes the matching earlier concern, issue or "
    "commitment. Do NOT list closed items as open or as current concerns; mention them "
    "under recent_changes and shift the agenda toward what is new (e.g. new interests).\n"
    "- Commitments or unresolved issues with no later RESOLVED memory are still open: list "
    "them under open_commitments, and under missed_followups if the follow-up looks overdue.\n"
    "- Use ONLY the recalled memories; never invent facts. Ignore memories about other people.\n"
    "- If there are no memories, say so in contact_context and give a short generic "
    "first-meeting brief based on the purpose.\n"
    "Return ONLY a JSON object with these keys: contact_context (string, 2-4 sentences), "
    "previous_discussions, open_commitments, missed_followups, current_concerns, "
    "recent_changes, suggested_agenda, suggested_questions, important_reminders (each a "
    "list of short strings), and how_memory_shaped_this_brief (list of strings, each in "
    "the form 'Recalled: <memory> -> Brief: <how it changed the brief>')."
)


def build_brief_prompt(
    contact_name: str,
    purpose: str,
    meeting_date: str,
    extra_context: str,
    memories: List[str],
) -> str:
    if memories:
        memory_block = "\n".join(f"{i}. {m}" for i, m in enumerate(memories, start=1))
    else:
        memory_block = "(no memories recalled - this contact has no history yet)"
    return (
        f"Contact: {contact_name}\nUpcoming meeting purpose: {purpose}\n"
        f"Meeting date: {meeting_date or 'not specified'}\n"
        f"Additional context: {extra_context or 'none'}\n\n"
        f"Memories recalled from Hindsight:\n{memory_block}\n\nReturn the JSON object now."
    )
