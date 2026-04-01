"""
pawpal_system.py
----------------
Logic layer for PawPal+.
Contains all backend classes: Owner, Pet, Task, and Scheduler.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care task."""

    name: str
    category: str                  # walk | feed | meds | grooming | enrichment
    duration_minutes: int
    priority: int                  # 1 = high, 2 = medium, 3 = low
    is_completed: bool = False

    def complete(self) -> None:
        """Mark this task as completed."""
        pass

    def __repr__(self) -> str:
        pass


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet with basic info and a list of care tasks."""

    name: str
    species: str
    breed: str
    age: int                                    # years
    special_needs: list[str] = field(default_factory=list)
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        pass

    def __repr__(self) -> str:
        pass


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner with a daily time budget and optional preferences."""

    def __init__(
        self,
        name: str,
        available_minutes: int,
        preferences: Optional[dict] = None,
    ) -> None:
        self.name = name
        self.available_minutes = available_minutes          # daily time budget
        self.preferences: dict = preferences or {}
        self._pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        pass

    def get_pets(self) -> list[Pet]:
        """Return all pets registered to this owner."""
        pass

    def __repr__(self) -> str:
        pass


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Generates a daily care plan for a pet.

    Strategy (to be implemented):
      - Sort tasks by priority (1 = high first), break ties by shortest duration.
      - Greedily add tasks until owner.available_minutes is exhausted.
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet

    def generate_plan(self) -> list[Task]:
        """
        Return an ordered list of tasks that fit within the owner's daily time budget.
        """
        pass

    def explain_plan(self, plan: list[Task]) -> str:
        """
        Return a human-readable explanation of why each task was included
        and flag any tasks that were left out due to time constraints.
        """
        pass

    def get_unscheduled(self, plan: list[Task]) -> list[Task]:
        """
        Return tasks that could not be fit into the plan.
        """
        pass
