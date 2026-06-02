"""Todo list manager backed by shared JSON storage."""

from core.storage import TODOS_FILE, load, save


def add_todo(task: str, priority: str = "medium") -> str:
    todos = load(TODOS_FILE)
    todos.append({"task": task, "done": False, "priority": priority})
    save(TODOS_FILE, todos)
    return f"Added to your list: {task}"


def complete_todo(task: str) -> str:
    todos = load(TODOS_FILE)
    task_to_match = task.strip().lower()

    found = False
    for item in todos:
        if str(item.get("task", "")).strip().lower() == task_to_match:
            item["done"] = True
            found = True
            break

    if not found:
        return f"Could not find task: {task}"

    save(TODOS_FILE, todos)
    return f"Marked as done: {task}"


def delete_todo(task: str) -> str:
    todos = load(TODOS_FILE)
    task_to_match = task.strip().lower()

    found = False
    for index, item in enumerate(todos):
        if str(item.get("task", "")).strip().lower() == task_to_match:
            todos.pop(index)
            found = True
            break

    if not found:
        return f"Could not find task: {task}"

    save(TODOS_FILE, todos)
    return f"Deleted: {task}"


def get_all() -> list:
    return load(TODOS_FILE)
