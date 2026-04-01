"""
pawpal_system.py
----------------
Logic layer for PawPal+.
Contains all backend classes: Owner, Pet, Task, and Scheduler.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, timedelta
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
    start_time: str = ""        # "HH:MM" — set by user or auto-assigned by Scheduler.assign_start_times()
    recurrence: str = ""        # "daily" | "weekly" | "" (empty = one-time task)
    due_date: Optional[date] = None  # date this task is due; defaults to today on first use

    def complete(self) -> Optional[Task]:
        """Mark this task as completed and return the next occurrence if it recurs.

        Returns a new Task with due_date advanced by timedelta(days=1) for daily tasks
        or timedelta(weeks=1) for weekly tasks. Returns None for one-time tasks.
        Caller (e.g. Pet.complete_task) is responsible for adding the new task.
        """
        self.is_completed = True
        if self.recurrence:
            return self.next_occurrence()
        return None

    def next_occurrence(self) -> Task:
        """Return a fresh copy of this task scheduled for its next due date.

        Uses timedelta to compute the next date:
          - 'daily'  → due_date + timedelta(days=1)
          - 'weekly' → due_date + timedelta(weeks=1)
        The new task starts with is_completed=False and no start_time assigned yet.
        """
        base = self.due_date or date.today()
        delta = timedelta(days=1) if self.recurrence == "daily" else timedelta(weeks=1)
        return Task(
            name=self.name,
            category=self.category,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recurrence=self.recurrence,
            due_date=base + delta,
        )

    def __repr__(self) -> str:
        status = "done" if self.is_completed else "pending"
        label  = PRIORITY_LABEL.get(self.priority, str(self.priority))
        time   = f", start={self.start_time}" if self.start_time else ""
        recur  = f", due={self.due_date}, recurrence={self.recurrence}" if self.recurrence else ""
        return (
            f"Task('{self.name}', category='{self.category}', "
            f"{self.duration_minutes}min, priority={label}{time}{recur}, {status})"
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

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task complete and automatically reschedule it if it recurs.

        Calls task.complete(), which returns the next Task instance for recurring
        tasks or None for one-time tasks. If a next occurrence is returned it is
        added to this pet's task list immediately.
        Returns the new Task (or None) so callers can inspect it if needed.
        """
        next_task = task.complete()
        if next_task is not None:
            self._tasks.append(next_task)
        return next_task

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
# Helpers
# ---------------------------------------------------------------------------

def _time_to_minutes(hhmm: str) -> int:
    """Convert a 'HH:MM' string to total minutes since midnight."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_time(total: int) -> str:
    """Convert total minutes since midnight back to a 'HH:MM' string."""
    h, m = divmod(total, 60)
    return f"{h:02d}:{m:02d}"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """
    Generates and organises a daily care plan for one pet.

    Core scheduling strategy:
      1. Filter out already-completed tasks.
      2. Sort by priority ascending (1 = high first).
      3. Break priority ties by shortest duration (fit more tasks in).
      4. Greedily add tasks until owner.available_minutes is exhausted.
      5. Auto-assign sequential start times to the plan (default start: 08:00).

    Additional utilities:
      - sort_by_time()     — sort any task list by their 'HH:MM' start_time.
      - filter_tasks()     — filter by completion status and/or category.
      - detect_conflicts() — find tasks whose time windows overlap.
      - get_recurring()    — return tasks marked as daily or weekly.
    """

    def __init__(self, owner: Owner, pet: Pet) -> None:
        self.owner = owner
        self.pet = pet
        # Snapshot at construction so the plan is stable during a session.
        self.tasks: list[Task] = pet.get_tasks()

    # ------------------------------------------------------------------ #
    # Primary planning methods                                            #
    # ------------------------------------------------------------------ #

    def generate_plan(self, start_hour: int = 8) -> list[Task]:
        """Return priority-sorted tasks that fit the time budget, with start times assigned."""
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

        self.assign_start_times(plan, start_hour=start_hour)
        return plan

    def explain_plan(self, plan: list[Task]) -> str:
        """Return a formatted string showing timed tasks, time used, and skipped tasks."""
        header = (
            f"Daily Plan for {self.pet.name} "
            f"(budget: {self.owner.available_minutes} min)\n"
            + "=" * 52
        )
        lines = [header]

        total_minutes = 0
        for i, task in enumerate(plan, 1):
            label    = PRIORITY_LABEL.get(task.priority, str(task.priority))
            time_str = f"[{task.start_time}]  " if task.start_time else "         "
            recur    = f"  ({task.recurrence})" if task.recurrence else ""
            lines.append(
                f"  {i}. {time_str}{task.name} [{task.category}]"
                f" — {task.duration_minutes} min  (priority: {label}){recur}"
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

    # ------------------------------------------------------------------ #
    # Sorting                                                             #
    # ------------------------------------------------------------------ #

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by their 'HH:MM' start_time; tasks with no time set go last.

        Uses a lambda as the sort key: converts 'HH:MM' to total minutes so
        string comparison is replaced by integer comparison — '09:30' < '10:05'.
        Tasks where start_time is empty are assigned a sentinel value (9999 min)
        so they always sort to the end of the list.
        """
        return sorted(
            tasks,
            key=lambda t: _time_to_minutes(t.start_time) if t.start_time else 9999,
        )

    # ------------------------------------------------------------------ #
    # Filtering                                                           #
    # ------------------------------------------------------------------ #

    def filter_tasks(
        self,
        tasks: list[Task],
        *,
        completed: Optional[bool] = None,
        category: Optional[str] = None,
    ) -> list[Task]:
        """Filter a task list by completion status and/or category.

        Pass completed=True  to see only finished tasks.
        Pass completed=False to see only pending tasks.
        Pass category='walk' to see only walk tasks.
        Filters are combined with AND when both are provided.
        """
        result = tasks
        if completed is not None:
            result = [t for t in result if t.is_completed == completed]
        if category is not None:
            result = [t for t in result if t.category == category]
        return result

    # ------------------------------------------------------------------ #
    # Recurring tasks                                                     #
    # ------------------------------------------------------------------ #

    def get_recurring(self) -> list[Task]:
        """Return tasks that repeat on a daily or weekly schedule."""
        return [t for t in self.tasks if t.recurrence in ("daily", "weekly")]

    # ------------------------------------------------------------------ #
    # Time assignment                                                     #
    # ------------------------------------------------------------------ #

    def assign_start_times(self, plan: list[Task], start_hour: int = 8) -> None:
        """Auto-assign sequential 'HH:MM' start times to each task in the plan.

        Tasks are assumed to run back-to-back with no gaps.
        Mutates each task's start_time in place.
        """
        cursor = start_hour * 60          # minutes since midnight
        for task in plan:
            task.start_time = _minutes_to_time(cursor)
            cursor += task.duration_minutes

    # ------------------------------------------------------------------ #
    # Conflict detection                                                  #
    # ------------------------------------------------------------------ #

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return pairs of tasks whose scheduled time windows overlap.

        Two tasks A and B conflict when:
            A.start < B.end  AND  B.start < A.end
        Only tasks that have a start_time set are checked.
        """
        timed = [
            (t, _time_to_minutes(t.start_time))
            for t in tasks if t.start_time
        ]

        conflicts: list[tuple[Task, Task]] = []
        for i, (task_a, start_a) in enumerate(timed):
            end_a = start_a + task_a.duration_minutes
            for task_b, start_b in timed[i + 1:]:
                end_b = start_b + task_b.duration_minutes
                if start_a < end_b and start_b < end_a:
                    conflicts.append((task_a, task_b))

        return conflicts
