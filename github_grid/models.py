from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum, auto
from typing import List


class ContributionLevel(Enum):
    NONE = auto()
    FIRST_QUARTILE = auto()
    SECOND_QUARTILE = auto()
    THIRD_QUARTILE = auto()
    FOURTH_QUARTILE = auto()


@dataclass(frozen=True)
class ContributionDay:
    date: date
    contribution_count: int
    level: ContributionLevel


@dataclass(frozen=True)
class ContributionWeek:
    days: List[ContributionDay]


@dataclass(frozen=True)
class ContributionData:
    total_contributions: int
    weeks: List[ContributionWeek]
    fetched_at: datetime
