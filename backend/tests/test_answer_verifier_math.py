import pytest

from services.answer_verifier import _extract_math_expression, _verify_math

@pytest.mark.asyncio
async def test_extract_math_expression_preserves_equals_and_unicode_dash():
    expression = _extract_math_expression('Solve 4(a – 3) = 22')
    assert expression == '4(a - 3) = 22'

@pytest.mark.asyncio
async def test_verify_math_equation_with_wrong_answer():
    assert await _verify_math('Solve 4(a – 3) = 22', '2') is False
    assert await _verify_math('Solve 4(a – 3) = 22', '8') is True
