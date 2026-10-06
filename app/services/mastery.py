from decimal import Decimal


def calculate_mastery(score: Decimal, correct: bool) -> Decimal:
    """Decimal arithmetic keeps seven correct answers exactly at the 0.70 boundary."""
    change = Decimal("0.10") if correct else Decimal("-0.05")
    return min(Decimal("1.00"), max(Decimal("0.00"), score + change))
