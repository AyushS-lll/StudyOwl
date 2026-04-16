"""
Hint engine — the core of StudyOwl.

Calls the Claude API to generate a Socratic hint at the appropriate level.
Never reveals the direct answer before Level 3 is exhausted.

Hint levels:
  1 — Socratic question only. No method hints.
  2 — Points to the relevant formula or concept. No solving.
  3 — Near-answer with all values filled in. Student must do the final step.
"""

from openai import AzureOpenAI
from config import settings

client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version="2024-10-01-preview",
    azure_endpoint=settings.azure_openai_endpoint,
)

HINT_SYSTEM = """
You are StudyOwl, a Socratic homework assistant. You NEVER give the direct answer.
Current hint level: {level}/3.

Level 1 — Ask exactly one Socratic question. Do not explain the method or hint at the formula.
Level 2 — Name the relevant formula or concept and explain what it means. Do not substitute values or solve.
Level 3 — Write out the formula with all known values substituted. Stop before the final answer. The student must perform the last calculation step themselves.

Subject area: {subject}

Rules:
- Maximum 3 sentences per response.
- Always end with exactly one short, genuine encouraging sentence.
- If the student expresses frustration or distress, acknowledge it warmly before the hint.
"""


def get_hint(
    question: str,
    subject: str,
    level: int,
    previous_attempts: list[str],
) -> str:
    """
    Generate a Socratic hint for the given question at the specified hint level.

    Args:
        question: The original homework question.
        subject: Classified subject area (math, science, english, history, other).
        level: Current hint level (1, 2, or 3).
        previous_attempts: List of the student's previous answer attempts.

    Returns:
        A hint string from Claude, appropriate to the hint level.
    """
    attempts_text = (
        "\n".join(f"- {a}" for a in previous_attempts)
        if previous_attempts
        else "None yet."
    )

    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        max_completion_tokens=300,
        messages=[
            {"role": "system", "content": HINT_SYSTEM.format(level=level, subject=subject)},
            {
                "role": "user",
                "content": (
                    f"Question: {question}\n\n"
                    f"Student's previous attempts:\n{attempts_text}"
                ),
            }
        ],
    )

    return response.choices[0].message.content.strip()


def detect_distress(message: str) -> bool:
    """
    Use Claude to detect if a student message signals genuine distress.
    Returns True if the student should trigger a teacher alert immediately.
    """
    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        max_completion_tokens=10,
        messages=[
            {
                "role": "system",
                "content": (
                    "You detect student distress in homework messages. "
                    "Reply with only 'yes' or 'no'. "
                    "Examples of distress: 'I give up', 'I don't understand anything', "
                    "'this makes no sense', 'I hate this', 'I can't do this'."
                ),
            },
            {"role": "user", "content": message},
        ],
    )
    return response.choices[0].message.content.strip().lower() == "yes"
