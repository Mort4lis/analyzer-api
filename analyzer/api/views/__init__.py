from .citizens import (
    CitizenListView,
    CitizenDetailView,
    CitizenBirthdayView
)
from .imports import ImportView
from .stats import TownAgeStatView

VIEWS = (
    ImportView,
    CitizenListView,
    CitizenDetailView,
    CitizenBirthdayView,
    TownAgeStatView
)
