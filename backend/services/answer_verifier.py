"""
Answer verifier — check if a student's answer is correct.

Uses SymPy for math; Claude for other subjects.
"""

from openai import AzureOpenAI
import re
import sympy
from config import settings

client = AzureOpenAI(
    api_key=settings.azure_openai_api_key,
    api_version="2024-10-01-preview",
    azure_endpoint=settings.azure_openai_endpoint,
)


def _extract_math_expression(question: str) -> str | None:
    """Try to convert a simple natural-language math question into a SymPy expression."""
    text = question.lower()
    text = text.replace("divided by", "/")
    text = text.replace("over", "/")
    text = text.replace("times", "*")
    text = text.replace("multiplied by", "*")
    text = text.replace("plus", "+")
    text = text.replace("minus", "-")
    text = text.replace("^", "**")
    text = text.replace("–", "-")
    text = text.replace("—", "-")
    text = text.replace("−", "-")
    text = re.sub(r"what is |calculate |evaluate |find |solve |the result of |answer is |equals?", "", text)
    text = re.sub(r"[^0-9a-zA-Z\.\+\-\*/\^\(\)= ]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return None
    return text


async def check(question: str, answer: str, subject: str) -> bool:
    """
    Verify if a student's answer is correct.

    For math: attempts symbolic verification with SymPy.
    For others: uses Claude to judge correctness.

    Args:
        question: The original homework question.
        answer: The student's answer text.
        subject: The question's subject area.

    Returns:
        True if the answer is correct, False otherwise.
    """
    if subject == "math":
        return await _verify_math(question, answer)
    else:
        return await _verify_with_claude(question, answer, subject)


async def _verify_math(question: str, answer: str) -> bool:
    """
    Verify math answers using SymPy when possible.
    Falls back to Claude for complex cases.
    """
    answer_clean = answer.strip().replace("x =", "").replace("Answer:", "").strip()
    if not answer_clean:
        return False

    question_expr = _extract_math_expression(question)
    if not question_expr:
        return await _verify_with_claude(question, answer, "math")

    try:
        sympy_expr = sympy.sympify(question_expr)
        if isinstance(sympy_expr, sympy.Equality):
            symbols = list(sympy_expr.free_symbols)
            if len(symbols) == 1:
                solution = sympy.solve(sympy_expr, symbols[0])
                if not solution:
                    return False
                actual = sympy.simplify(sympy.sympify(answer_clean))
                return any(sympy.simplify(actual - sol) == 0 for sol in solution)
            return False

        expected = sympy.simplify(sympy_expr)
        actual = sympy.simplify(sympy.sympify(answer_clean))
        return sympy.simplify(expected - actual) == 0
    except (sympy.SympifyError, ValueError):
        return await _verify_with_claude(question, answer, "math")


async def _verify_with_claude(question: str, answer: str, subject: str) -> bool:
    """
    Use Claude to verify if an answer is correct.
    """
    response = client.chat.completions.create(
        model=settings.azure_openai_deployment,
        max_completion_tokens=50,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert homework grader. "
                    "Evaluate if the student's answer to the question is correct. "
                    "Respond with ONLY 'yes' or 'no'. Accept reasonable variations and rounding."
                ),
            },
            {
                "role": "user",
                "content": f"Question: {question}\n\nStudent's answer: {answer}",
            }
        ],
    )
    return response.choices[0].message.content.strip().lower() == "yes"
