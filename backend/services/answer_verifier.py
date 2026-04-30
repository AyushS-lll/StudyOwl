"""
Answer verifier — check if a student's answer is correct.

Uses SymPy for math; Claude for other subjects.
"""

from openai import AzureOpenAI
import re
import sympy
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application
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
    # Clean up the answer: remove common prefixes (with or without space)
    answer_clean = answer.strip()
    for prefix in ["a =", "a=", "x =", "x=", "y =", "y=", "z =", "z=", "Answer:", "answer:", "The answer is"]:
        if answer_clean.lower().startswith(prefix.lower()):
            answer_clean = answer_clean[len(prefix):].strip()
    
    answer_clean = answer_clean.strip()
    if not answer_clean:
        return False

    question_expr = _extract_math_expression(question)
    if not question_expr:
        return await _verify_with_claude(question, answer, "math")

    try:
        # Check if equation has "=" sign
        if "=" in question_expr:
            parts = question_expr.split("=")
            if len(parts) != 2:
                return await _verify_with_claude(question, answer, "math")
            
            left_expr = parts[0].strip()
            right_expr = parts[1].strip()
            
            # Parse both sides with implicit multiplication
            left = parse_expr(left_expr, transformations=(standard_transformations + (implicit_multiplication_application,)))
            right = parse_expr(right_expr, transformations=(standard_transformations + (implicit_multiplication_application,)))
            
            # Get the variable to solve for
            symbols = left.free_symbols | right.free_symbols
            if len(symbols) != 1:
                return await _verify_with_claude(question, answer, "math")
            
            var = list(symbols)[0]
            equation = sympy.Eq(left, right)
            solution = sympy.solve(equation, var)
            
            if not solution:
                return False
            
            # Parse and compare the student's answer
            try:
                actual = sympy.sympify(answer_clean)
            except (sympy.SympifyError, ValueError, TypeError):
                return False
            
            # Check if actual matches any solution (with numerical tolerance)
            for sol in solution:
                try:
                    sol_val = float(sympy.simplify(sol))
                    actual_val = float(sympy.simplify(actual))
                    # Allow small floating-point errors (1e-9)
                    if abs(sol_val - actual_val) < 1e-9:
                        return True
                except (TypeError, ValueError):
                    # If conversion to float fails, try symbolic comparison
                    if sympy.simplify(actual - sol) == 0:
                        return True
            return False
        else:
            # Expression without equation (evaluate both sides)
            expected = parse_expr(question_expr, transformations=(standard_transformations + (implicit_multiplication_application,)))
            actual = sympy.sympify(answer_clean)
            return sympy.simplify(expected - actual) == 0
    except (sympy.SympifyError, ValueError, TypeError):
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
