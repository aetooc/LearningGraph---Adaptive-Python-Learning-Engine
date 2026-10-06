from decimal import Decimal

import pytest

from app.services.mastery import calculate_mastery


@pytest.mark.parametrize("score,correct,expected", [
    ("0.00", True, "0.10"),
    ("0.10", False, "0.05"),
    ("0.95", True, "1.00"),
    ("0.02", False, "0.00"),
    ("0.00", False, "0.00"),
])
def test_mastery_update_and_clamping(score, correct, expected):
    assert calculate_mastery(Decimal(score), correct) == Decimal(expected)


def test_seven_correct_answers_reach_threshold_exactly():
    score = Decimal("0")
    for _ in range(7):
        score = calculate_mastery(score, True)
    assert score == Decimal("0.70")
