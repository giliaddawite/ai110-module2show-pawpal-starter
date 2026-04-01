"""
pawpal_system.py
----------------
Logic layer for PawPal+.
Contains all backend classes: Owner, Pet, Task, and Scheduler.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

# Maps the UI string labels to internal integer priority values.
# 1 = highest urgency; used for sorting in Scheduler.
PRIORITY_MAP: dict[str, int] = {"high": 1, "medium": 2, "low": 3}
PRIORITY_LABEL: dict[int, str] = {1: "high", 2: "medium", 3: "low"}

VALID_CATEGORIES = {"walk", "feed", "meds", "grooming", "enrichment"}


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care task."""

    name: str
    category: str           # walk | feed | meds | grooming | enrichment
    duration_minutes: int
    priority: int           # 1 = high, 2 = medium, 3 = low  (use PRIORITY_MAP to convert from UI strings)
    is_completed: bool = False

    def complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def __repr__(self) -> str:
        status = "done" if self.is_completed else "pending"
        label = PRIORITY_LABEL.get(self.priority, str(self.priority))
        return (
            f"Task('{self.name}', category='{self.category}', "
            f"{self.duration_minutes}min, priority={label}, {status})"
        )


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet with basic info and a list of care tasks."""

    name: str
    species: str
    breed: str
    age: int                                        # years
    special_needs: list[str] = field(default_factory=list)
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> None:
        """Add a care task for this pet."""
        self._tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return a copy of all tasks for this pet."""
        return list(self._tasks)

    def __repr__(self) -> str:
        needs = f", special_needs={self.special_needs}" if self.special_needs else ""
        return (
            f"Pet('{self.name}', {self.species}, {self.breed}, "
            f"age={self.age}{needs}, tasks={len(self._tasks)})"
        )


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
        self.available_minutes = available_minutes      # daily time budget
        self.preferences: dict = preferences or {}
        self._pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self._pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return a copy of all pets registered to this owner."""
        return list(self._pets)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        tasks: list[Task] = []
        for pet in self._pets:
            tasks.extend(pet.get_tasks())
        return tasks

    def __repr__(self) -> str:
        return (
            f"Owner('{self.name}', available={self.available_minutes}min, "
            f"pets={len(self._pets)})"
        )


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Generates a daily care plan for one pet.

    How it talks to Owner and Pet:
      - Receives an Owner (for the time budget) and a Pet (for the task list).
      - Calls pet.get_tasks() at construction time to snapshot the task list.
      - For multi-pet scenarios, owner.get_all_tasks() is available.

    Scheduling strategy:
      1. Filter out already-completed tasks.
      2. Sort by priority ascending (1 = high first).
      3. Break priority ties by shortest duration (fit more tasks in).
      4. Greedily add tasks until owner.available_minutes is exhausted.
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        # Snapshot at construction so the plan is stable during a session.
        self.tasks: list[Task] = pet.get_tasks()

    def generate_plan(self) -> list[Task]:
        """Return priority-sorted tasks that fit within the owner's daily time budget."""
        candidates = sorted(
            [t for t in self.tasks if not t.is_completed],
            key=lambda t: (t.priority, t.duration_minutes),
        )

        plan: list[Task] = []
        remaining = self.owner.available_minutes

        for task in candidates:
            if task.duration_minutes <= remaining:
                plan.append(task)
                remaining -= task.duration_minutes

        return plan

    def explain_plan(self, plan: list[Task]) -> str:
        """Return a formatted string showing scheduled tasks, time used, and skipped tasks."""
        header = (
            f"Daily Plan for {self.pet.name} "
            f"(budget: {self.owner.available_minutes} min)\n"
            + "=" * 52
        )
        lines = [header]

        total_minutes = 0
        for i, task in enumerate(plan, 1):
            label = PRIORITY_LABEL.get(task.priority, str(task.priority))
            lines.append(
                f"  {i}. {task.name} [{task.category}]"
                f" — {task.duration_minutes} min  (priority: {label})"
            )
            total_minutes += task.duration_minutes

        lines.append(
            f"\n  Scheduled: {total_minutes} min"
            f" / {self.owner.available_minutes} min available"
            f"  ({self.owner.available_minutes - total_minutes} min unused)"
        )

        skipped = self.get_unscheduled(plan)
        if skipped:
            lines.append("\n  Skipped — not enough time remaining:")
            for task in skipped:
                label = PRIORITY_LABEL.get(task.priority, str(task.priority))
                lines.append(
                    f"    - {task.name} ({task.duration_minutes} min, priority: {label})"
                )
        else:
            lines.append("\n  All pending tasks fit within the time budget.")

        return "\n".join(lines)

    def get_unscheduled(self, plan: list[Task]) -> list[Task]:
        """Return pending tasks that were excluded from the plan due to time constraints."""
        scheduled_ids = {id(t) for t in plan}
        return [
            t for t in self.tasks
            if id(t) not in scheduled_ids and not t.is_completed
        ]
