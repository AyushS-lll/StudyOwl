"""
Subject router — classify questions into subject areas.

Uses Claude to categorize incoming questions.
"""

from openai import AzureOpenAI
from config import settings

client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version="2024-10-01-preview",
    azure_endpoint=settings.azure_openai_endpoint,
)

SUBJECT_SYSTEM = """
You classify homework questions into one of exactly 5 categories.
Respond with ONLY the category name, nothing else.

Categories:
- math: algebra, geometry, calculus, trigonometry, statistics, equations, numbers
- science: physics, chemistry, biology, earth science, astronomy
- english: literature, grammar, writing, reading comprehension, essays
- history: dates, events, historical figures, civilizations, timelines
- other: anything that doesn't fit above

IMPORTANT: Reply with ONLY the category word (e.g., 'math', 'science', etc). No explanation.
"""


async def classify(question: str) -> str:
    """
    Classify a homework question into a subject area.

    Args:
        question: The homework question text.

    Returns:
        One of: 'math', 'science', 'english', 'history', 'other'.
    """
    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        max_completion_tokens=10,
        messages=[
            {"role": "system", "content": SUBJECT_SYSTEM},
            {"role": "user", "content": question},
        ],
    )
    subject = response.choices[0].message.content.strip().lower()
    # Ensure it's a valid subject
    valid_subjects = ["math", "science", "english", "history", "other"]
    return subject if subject in valid_subjects else "other"
