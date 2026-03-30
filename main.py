"""
PawPal+ CLI Demo
Run:  python main.py
"""

from datetime import datetime, date
from pawpal_system import Task, Pet, Owner, Scheduler

TODAY = date.today()

def make_dt(hour: int, minute: int = 0) -> datetime:
    """Helper — build a datetime on today's date at a given hour."""
    return datetime(TODAY.year, TODAY.month, TODAY.day, hour, minute)


# ── 1. Create an owner ────────────────────────────────────────────────────────
owner = Owner(name="Alex Johnson", email="alex@email.com", phone="555-1234")

# ── 2. Create pets ────────────────────────────────────────────────────────────
buddy = Pet(name="Buddy",  species="Dog", breed="Labrador",       age=3)
luna  = Pet(name="Luna",   species="Cat", breed="Siamese",         age=5)

owner.add_pet(buddy)
owner.add_pet(luna)

# ── 3. Add tasks to Buddy ─────────────────────────────────────────────────────
buddy.add_task(Task(
    task_type="feeding",
    description="Morning kibble",
    scheduled_time=make_dt(7, 30),
    duration_minutes=15,
    recurrence="daily",
))

buddy.add_task(Task(
    task_type="walk",
    description="Morning walk around the block",
    scheduled_time=make_dt(8, 0),
    duration_minutes=30,
    recurrence="daily",
))

buddy.add_task(Task(
    task_type="medication",
    description="Flea & tick tablet",
    scheduled_time=make_dt(8, 15),   # ← overlaps with the walk → conflict!
    duration_minutes=5,
    recurrence="monthly",
))

buddy.add_task(Task(
    task_type="appointment",
    description="Annual vet check-up",
    scheduled_time=make_dt(14, 0),
    duration_minutes=60,
))

# ── 4. Add tasks to Luna ──────────────────────────────────────────────────────
luna.add_task(Task(
    task_type="feeding",
    description="Wet food — tuna flavour",
    scheduled_time=make_dt(7, 0),
    duration_minutes=10,
    recurrence="daily",
))

luna.add_task(Task(
    task_type="medication",
    description="Hairball remedy paste",
    scheduled_time=make_dt(9, 0),
    duration_minutes=5,
    recurrence="weekly",
))

# ── 5. Run the scheduler ──────────────────────────────────────────────────────
scheduler = Scheduler(owner=owner, target_date=TODAY)
scheduler.print_schedule()

# ── 6. Show upcoming recurring tasks (next 3 days) ───────────────────────────
upcoming = scheduler.generate_recurring_tasks(days_ahead=3)
print(f"{len(upcoming)} recurring task(s) projected over the next 3 days.\n")

# ── 7. Mark a task complete and reprint ───────────────────────────────────────
print("  → Marking Luna's feeding as complete...\n")
luna.tasks[0].mark_complete()
scheduler.print_schedule()