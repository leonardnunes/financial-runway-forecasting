"""Validated input models for financial runway forecasting."""

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
import re


_PERIOD_PATTERN = re.compile(r"[0-9]{4}-(0[1-9]|1[0-2])")


def parse_nonnegative_decimal(
    value: Decimal | str,
    field_name: str,
) -> Decimal:
    """Validate a finite, nonnegative decimal input."""
    if not isinstance(value, (Decimal, str)):
        raise TypeError(
            f"{field_name} must be a Decimal or decimal string."
        )

    if isinstance(value, str) and not value.strip():
        raise ValueError(f"{field_name} cannot be empty.")

    try:
        result = Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(
            f"{field_name} must contain a valid decimal value."
        ) from exc

    if not result.is_finite():
        raise ValueError(f"{field_name} must be finite.")

    if result < 0:
        raise ValueError(f"{field_name} cannot be negative.")

    return result


def validate_period(period: str) -> str:
    """Validate a canonical YYYY-MM calendar period."""
    if not isinstance(period, str):
        raise TypeError("Period must be a string.")

    if _PERIOD_PATTERN.fullmatch(period) is None:
        raise ValueError("Period must use YYYY-MM format.")

    if int(period[:4]) == 0:
        raise ValueError("Calendar year must be at least 0001.")

    return period


@dataclass(frozen=True, slots=True)
class MonthlyRecord:
    """Historical monthly revenue and expenses."""

    period: str
    revenue: Decimal | str
    expenses: Decimal | str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "period",
            validate_period(self.period),
        )
        object.__setattr__(
            self,
            "revenue",
            parse_nonnegative_decimal(
                self.revenue,
                "revenue",
            ),
        )
        object.__setattr__(
            self,
            "expenses",
            parse_nonnegative_decimal(
                self.expenses,
                "expenses",
            ),
        )


@dataclass(frozen=True, slots=True)
class Scenario:
    """Revenue and expense multipliers for a projection."""

    name: str
    revenue_multiplier: Decimal | str
    expense_multiplier: Decimal | str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Scenario name cannot be empty.")

        object.__setattr__(self, "name", self.name.strip())

        object.__setattr__(
            self,
            "revenue_multiplier",
            parse_nonnegative_decimal(
                self.revenue_multiplier,
                "revenue_multiplier",
            ),
        )
        object.__setattr__(
            self,
            "expense_multiplier",
            parse_nonnegative_decimal(
                self.expense_multiplier,
                "expense_multiplier",
            ),
        )
