# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

---

## Smarter Scheduling

Beyond basic priority-based planning, `pawpal_system.py` includes several algorithmic features:

### Sort by time
`Scheduler.sort_by_time(tasks)` sorts any task list by its `HH:MM` start time using a lambda key that converts the string to total minutes — so `"09:05"` correctly sorts before `"10:00"` via integer comparison, not string comparison.

### Filter by status or category
`Scheduler.filter_tasks(tasks, completed=, category=)` lets you slice the task list by completion status, category (walk / feed / meds / grooming / enrichment), or both at once. Useful for showing only today's pending tasks or only medication reminders.

### Auto-assign start times
`Scheduler.assign_start_times(plan, start_hour=8)` walks through the generated plan and stamps each task with a sequential `HH:MM` start time, assuming tasks run back-to-back from the given hour (default 08:00).

### Conflict detection
`Scheduler.detect_conflicts(tasks)` scans all tasks that have a `start_time` set and returns every pair whose time windows overlap — using the interval overlap condition `A.start < B.end AND B.start < A.end`.

### Recurring tasks
Tasks can be marked `recurrence="daily"` or `recurrence="weekly"`. When `pet.complete_task(task)` is called, it uses Python's `timedelta` to calculate the next due date (`+1 day` or `+7 days`) and automatically appends a fresh copy of the task to the pet's task list — no manual rescheduling required.

### Run the CLI demo
```bash
python main.py
```
