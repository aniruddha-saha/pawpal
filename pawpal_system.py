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
    "medication":  1,
    "appointment": 2,
    "walk":        3,
    "feeding":     4,
}

RECURRENCE_OPTIONS = ["none", "daily", "weekly", "monthly"]


# ─────────────────────────────────────────────────────────────────────────────
#  TASK
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Task:
    """Represents a single care task assigned to a pet."""

    task_type: str          # "feeding" | "walk" | "medication" | "appointment"
    description: str
    scheduled_time: datetime
    duration_minutes: int = 30
    recurrence: str = "none"   # "none" | "daily" | "weekly" | "monthly"
    is_complete: bool = False
    task_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])

    # ── computed ──────────────────────────────────────────────────────────────
    @property
    def priority(self) -> int:
        """Return numeric priority; lower = more urgent."""
        return PRIORITY.get(self.task_type, 99)

    # ── methods ───────────────────────────────────────────────────────────────
    def is_recurring(self) -> bool:
        """Return True if this task repeats on a schedule."""
        return self.recurrence != "none"

    def get_next_occurrence(self) -> Optional[datetime]:
        """Calculate the next datetime based on the recurrence rule."""
        if not self.is_recurring():
            return None
        if self.recurrence == "daily":
            return self.scheduled_time + timedelta(days=1)
        if self.recurrence == "weekly":
            return self.scheduled_time + timedelta(weeks=1)
        if self.recurrence == "monthly":
            return self.scheduled_time + timedelta(days=30)
        return None

    def mark_complete(self):
        """Mark this task as finished."""
        self.is_complete = True

    def __str__(self):
        status = "✓" if self.is_complete else "○"
        recur  = f" [{self.recurrence}]" if self.is_recurring() else ""
        return (
            f"  [{status}] {self.scheduled_time.strftime('%I:%M %p')} | "
            f"{self.task_type.upper():<12} | {self.description}{recur}"
        )


# ─────────────────────────────────────────────────────────────────────────────
#  PET
# ─────────────────────────────────────────────────────────────────────────────
@dataclass
class Pet:
    """Represents a pet with its profile and list of care tasks."""

    name: str
    species: str
    breed: str
    age: int
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task):
        """Append a new task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        """Remove a task by ID; returns True if the task was found."""
        before = len(self.tasks)
        self.tasks = [t for t in self.tasks if t.task_id != task_id]
        return len(self.tasks) < before

    def get_tasks_by_type(self, task_type: str) -> List[Task]:
        """Return all tasks matching the given type string."""
        return [t for t in self.tasks if t.task_type == task_type]

    def __str__(self):
        return f"{self.name} ({self.species}, {self.breed}, age {self.age})"


# ─────────────────────────────────────────────────────────────────────────────
#  OWNER
# ─────────────────────────────────────────────────────────────────────────────
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
        """Remove a pet by name; returns True if the pet was found."""
        before = len(self.pets)
        self.pets = [p for p in self.pets if p.name != pet_name]
        return len(self.pets) < before

    def get_all_tasks(self) -> List[Task]:
        """Collect and return every task across all pets."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Find and return a pet by name, or None if not found."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def __str__(self):
        return f"{self.name} | {len(self.pets)} pet(s) registered"


# ─────────────────────────────────────────────────────────────────────────────
#  SCHEDULER
# ─────────────────────────────────────────────────────────────────────────────
class Scheduler:
    """
    The scheduling brain of PawPal+.
    Retrieves tasks from the Owner's pets, then sorts, filters,
    detects conflicts, and expands recurring tasks.
    """

    def __init__(self, owner: Owner, target_date: Optional[date] = None):
        """Initialise the scheduler for an owner on a specific date (default: today)."""
        self.owner = owner
        self.target_date = target_date or date.today()

    # ── core retrieval ────────────────────────────────────────────────────────
    def get_daily_tasks(self) -> List[Task]:
        """Return incomplete tasks from all pets that fall on target_date."""
        return [
            task
            for task in self.owner.get_all_tasks()
            if task.scheduled_time.date() == self.target_date
            and not task.is_complete
        ]

    def get_tasks_for_pet(self, pet_name: str) -> List[Task]:
        """Return today's incomplete tasks for a single named pet."""
        pet = self.owner.get_pet(pet_name)
        if not pet:
            return []
        return [
            t for t in pet.tasks
            if t.scheduled_time.date() == self.target_date and not t.is_complete
        ]

    # ── algorithmic logic ─────────────────────────────────────────────────────
    def sort_by_priority(self) -> List[Task]:
        """
        Sort today's tasks by:
          1. Priority level  (medication=1 → feeding=4)
          2. Scheduled time  (earlier first within same priority)
        """
        return sorted(self.get_daily_tasks(),
                      key=lambda t: (t.priority, t.scheduled_time))

    def detect_conflicts(self) -> List[tuple]:
        """
        Identify pairs of tasks whose time windows overlap.
        Overlap condition: task A starts before task B ends AND
                           task B starts before task A ends.
        Returns a list of (Task, Task) conflict pairs.
        """
        tasks = self.sort_by_priority()
        conflicts = []
        for i in range(len(tasks)):
            for j in range(i + 1, len(tasks)):
                a, b = tasks[i], tasks[j]
                a_end = a.scheduled_time + timedelta(minutes=a.duration_minutes)
                b_end = b.scheduled_time + timedelta(minutes=b.duration_minutes)
                if a.scheduled_time < b_end and b.scheduled_time < a_end:
                    conflicts.append((a, b))
        return conflicts

    def generate_recurring_tasks(self, days_ahead: int = 7) -> List[Task]:
        """
        Project recurring tasks forward up to days_ahead days from target_date.
        Returns new Task objects without modifying the originals.
        """
        generated = []
        cutoff = datetime.combine(
            self.target_date + timedelta(days=days_ahead),
            datetime.max.time()
        )
        for task in self.owner.get_all_tasks():
            if not task.is_recurring():
                continue
            next_time = task.get_next_occurrence()
            while next_time and next_time <= cutoff:
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

    # ── display ───────────────────────────────────────────────────────────────
    def print_schedule(self):
        """Pretty-print today's prioritised schedule and any conflicts."""
        tasks     = self.sort_by_priority()
        conflicts = self.detect_conflicts()
        width     = 54

        print("\n" + "=" * width)
        print(f"  🐾 PawPal+ Schedule — {self.target_date.strftime('%A, %b %d %Y')}")
        print(f"  Owner : {self.owner.name}")
        print("=" * width)

        if not tasks:
            print("  No tasks scheduled for today. Enjoy the day!")
        else:
            current_priority = None
            labels = {1: " MEDICATIONS", 2: " APPOINTMENTS",
                      3: " WALKS", 4: "  FEEDINGS", 99: " OTHER"}
            for task in tasks:
                if task.priority != current_priority:
                    current_priority = task.priority
                    print(f"\n  {labels.get(task.priority, 'OTHER')}")
                    print(f"  {'-' * (width - 4)}")
                # find which pet owns this task
                pet_name = "Unknown"
                for pet in self.owner.pets:
                    if task in pet.tasks:
                        pet_name = pet.name
                        break
                print(f"{task}  [{pet_name}]")

        if conflicts:
            print(f"\n   {len(conflicts)} scheduling conflict(s) detected:")
            for a, b in conflicts:
                print(f"     • '{a.description}' overlaps '{b.description}'")

        print("=" * width + "\n")