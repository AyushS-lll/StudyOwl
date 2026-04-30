import pytest

from services.answer_verifier import _extract_math_expression, _verify_math

@pytest.mark.asyncio
async def test_extract_math_expression_preserves_equals_and_unicode_dash():
    expression = _extract_math_expression('Solve 4(a – 3) = 22')
    assert expression == '4(a - 3) = 22'

@pytest.mark.asyncio
async def test_verify_math_equation_4a_minus_3_equals_22():
    """Test: 4(a – 3) = 22 → a = 8.5"""
    # Correct answer: 8.5
    assert await _verify_math('Solve 4(a – 3) = 22', '8.5') is True
    assert await _verify_math('Solve 4(a – 3) = 22', '17/2') is True
    # Wrong answers
    assert await _verify_math('Solve 4(a – 3) = 22', '2') is False
    assert await _verify_math('Solve 4(a – 3) = 22', '7') is False
    assert await _verify_math('Solve 4(a – 3) = 22', '8') is False

@pytest.mark.asyncio
async def test_verify_math_equation_4a_minus_15_equals_25():
    """Test: 4a - 15 = 25 → a = 10"""
    # Correct answer: 10
    assert await _verify_math('Solve 4a - 15 = 25', '10') is True
    # Wrong answers
    assert await _verify_math('Solve 4a - 15 = 25', '7') is False
    assert await _verify_math('Solve 4a - 15 = 25', '9') is False
    assert await _verify_math('Solve 4a - 15 = 25', '11') is False

@pytest.mark.asyncio
async def test_verify_math_with_answer_prefix():
    """Test that common answer prefixes are stripped correctly"""
    assert await _verify_math('Solve 4(a – 3) = 22', 'a = 8.5') is True
    assert await _verify_math('Solve 4(a – 3) = 22', 'a=8.5') is True
    assert await _verify_math('Solve 4a - 15 = 25', 'a = 10') is True
