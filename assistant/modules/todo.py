"""Todo list manager backed by shared JSON storage."""

from core.storage import TODOS_FILE, load, save


def add_todo(task: str) -> str:
    # Load existing todos, append a new pending item, and persist changes.
    todos = load(TODOS_FILE)
    todos.append({"task": task, "done": False})
    save(TODOS_FILE, todos)
    return f"Added to your list: {task}"


def complete_todo(task: str) -> str:
    # Mark the first case-insensitive task match as done and save the list.
    todos = load(TODOS_FILE)
    task_to_match = task.strip().lower()

    for item in todos:
        if str(item.get("task", "")).strip().lower() == task_to_match:
            item["done"] = True
            break

    save(TODOS_FILE, todos)
    return f"Marked as done: {task}"


def delete_todo(task: str) -> str:
    # Remove the first case-insensitive task match and save the updated list.
    todos = load(TODOS_FILE)
    task_to_match = task.strip().lower()

    for index, item in enumerate(todos):
        if str(item.get("task", "")).strip().lower() == task_to_match:
            todos.pop(index)
            break

    save(TODOS_FILE, todos)
    return f"Deleted: {task}"


def get_all() -> list:
    # Return all stored todo items.
    return load(TODOS_FILE)
