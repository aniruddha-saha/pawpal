classDiagram
    class Owner {
        +String name
        +String email
        +String phone
        +List~Pet~ pets
        +add_pet(pet: Pet)
        +remove_pet(pet_name: str)
        +get_all_tasks() List~Task~
    }

    class Pet {
        +String name
        +String species
        +String breed
        +int age
        +List~Task~ tasks
        +add_task(task: Task)
        +remove_task(task_id: str)
        +get_tasks_by_type(task_type: str) List~Task~
    }

    class Task {
        +String task_id
        +String task_type
        +String description
        +datetime scheduled_time
        +int duration_minutes
        +int priority
        +String recurrence
        +bool is_complete
        +is_recurring() bool
        +get_next_occurrence() datetime
        +mark_complete()
    }

    class Schedule {
        +Owner owner
        +date target_date
        +get_daily_tasks() List~Task~
        +sort_by_priority() List~Task~
        +detect_conflicts() List~tuple~
        +generate_recurring_tasks()
    }

    Owner "1" --> "0..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Schedule "1" --> "1" Owner : manages
    Schedule ..> Task : organizes