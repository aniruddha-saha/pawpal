"""
PawPal+ System — Core Logic Layer
All backend classes live here. No UI code in this file.
"""

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import List, Optional
import uuid


# ── Priority constants (lower number = higher priority) ──────────────────────
PRIORITY = {
    "medication":   1,
    "appointment":  2,
    "walk":         3,
    "feeding":      4,
}

# ── Recurrence options ────────────────────────────────────────────────────────
RECURRENCE_OPTIONS = ["none", "daily", "weekly", "monthly"]


@dataclass
class Task:
    """Represents a single care task assigned to a pet."""
    task_type: str                        # "feeding" | "walk" | "medication" | "appointment"
    description: str
    scheduled_time: datetime
    duration_minutes: int = 30
    recurrence: str = "none"              # "none" | "daily" | "weekly" | "monthly"
    is_complete: bool = False
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    @property
    def priority(self) -> int:
        """Lower number = higher priority."""
        return PRIORITY.get(self.task_type, 99)

    def is_recurring(self) -> bool:
        """Returns True if this task repeats on a schedule."""
        return self.recurrence != "none"

    def get_next_occurrence(self) -> Optional[datetime]:
        """Calculate the next scheduled time based on recurrence rule."""
        if not self.is_recurring():
            return None
        if self.recurrence == "daily":
            return self.scheduled_time + timedelta(days=1)
        if self.recurrence == "weekly":
            return self.scheduled_time + timedelta(weeks=1)
        if self.recurrence == "monthly":
            # Simple 30-day approximation
            return self.scheduled_time + timedelta(days=30)
        return None

    def mark_complete(self):
        """Mark this task as done."""
        self.is_complete = True

    def __repr__(self):
        status = "✓" if self.is_complete else "○"
        return (f"[{status}] {self.task_type.upper()} — {self.description} "
                f"@ {self.scheduled_time.strftime('%H:%M')} (priority {self.priority})")


@dataclass
class Pet:
    """Represents a pet owned by an Owner."""
    name: str
    species: str
    breed: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Add a care task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID. Returns True if found and removed."""
        original_len = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        return len(self.tasks) < original_len

    def get_tasks_by_type(self, task_type: str) -> List[Task]:
        """Filter tasks by type (e.g., 'walk', 'medication')."""
        return [t for t in self.tasks if t.task_type == task_type]

    def __repr__(self):
        return f"Pet({self.name}, {self.species}, age {self.age})"


@dataclass
class Owner:
    """Represents a pet owner who manages one or more pets."""
    name: str
    email: str
    phone: str = ""
    pets: List[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet):
        """Register a new pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        original_len = len(self.pets)
        self.pets = [p for p in self.pets if p.name != pet_name]
        return len(self.pets) < original_len

    def get_all_tasks(self) -> List[Task]:
        """Collect every task across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def __repr__(self):
        return f"Owner({self.name}, {len(self.pets)} pet(s))"


class Schedule:
    """
    The scheduling brain of PawPal+.
    Collects, sorts, and analyzes tasks for a given owner and date.
    """

    def __init__(self, owner: Owner, target_date: date):
        self.owner = owner
        self.target_date = target_date

    def get_daily_tasks(self) -> List[Task]:
        """Return all tasks scheduled for target_date, incomplete only."""
        return [
            task
            for task in self.owner.get_all_tasks()
            if task.scheduled_time.date() == self.target_date
            and not task.is_complete
        ]

    def sort_by_priority(self) -> List[Task]:
        """
        Sort today's tasks by:
        1. Priority level (medication first, feeding last)
        2. Scheduled time (earlier tasks first within same priority)
        """
        daily = self.get_daily_tasks()
        return sorted(daily, key=lambda t: (t.priority, t.scheduled_time))

    def detect_conflicts(self) -> List[tuple]:
        """
        Find pairs of tasks that overlap in time.
        A conflict occurs when task A ends after task B starts (and vice versa).
        Returns a list of (task_a, task_b) conflict pairs.
        """
        tasks = self.sort_by_priority()
        conflicts = []
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i], tasks[j]
                a_end = a.scheduled_time + timedelta(minutes=a.duration_minutes)
                b_end = b.scheduled_time + timedelta(minutes=b.duration_minutes)
                # Overlap condition: each starts before the other ends
                if a.scheduled_time < b_end and b.scheduled_time < a_end:
                    conflicts.append((a, b))
        return conflicts

    def generate_recurring_tasks(self, days_ahead: int = 7) -> List[Task]:
        """
        Project recurring tasks forward by `days_ahead` days.
        Returns new Task objects (does NOT mutate existing tasks).
        """
        generated = []
        for task in self.owner.get_all_tasks():
            if not task.is_recurring():
                continue
            next_time = task.get_next_occurrence()
            limit = datetime.combine(
                self.target_date + timedelta(days=days_ahead), datetime.min.time()
            )
            while next_time and next_time <= limit:
                new_task = Task(
                    task_type=task.task_type,
                    description=task.description,
                    scheduled_time=next_time,
                    duration_minutes=task.duration_minutes,
                    recurrence=task.recurrence,
                )
                generated.append(new_task)
                next_time = new_task.get_next_occurrence()
        return generated

    def print_schedule(self):
        """Pretty-print today's sorted schedule to the terminal."""
        tasks = self.sort_by_priority()
        conflicts = self.detect_conflicts()
        print(f"\n{'='*50}")
        print(f"Schedule for {self.target_date} — {self.owner.name}")
        print(f"{'='*50}")
        if not tasks:
            print("  No tasks scheduled for today.")
        for task in tasks:
            print(f"  {task}")
        if conflicts:
            for a, b in conflicts:
                print(f"     • '{a.description}' overlaps with '{b.description}'")
        print(f"{'='*50}\n")