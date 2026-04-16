import pytest

from services.answer_verifier import _verify_math

@pytest.mark.asyncio
async def test_verify_math_equation_solution():
    assert await _verify_math('Solve x + 4 = 19.', '15') is True
    assert await _verify_math('Solve x + 4 = 19.', '16') is False

@pytest.mark.asyncio
async def test_verify_math_simple_expression():
    assert await _verify_math('What is 3 + 2?', '5') is True
    assert await _verify_math('What is 3 + 2?', '4') is False
