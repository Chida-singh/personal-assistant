"""Personal notes module for storing and recalling relationship details."""

from core.storage import GIRLFRIEND_FILE, load, save


def _suggestion_for_key(key: str) -> str:
    # Provide a simple action suggestion for commonly saved note types.
    text = key.strip().lower()
    if "birthday" in text:
        return "Suggestion: Set a reminder and plan a thoughtful surprise."
    if "anniversary" in text:
        return "Suggestion: Plan quality time or a small celebration together."
    if "food" in text or "favourite" in text or "favorite" in text:
        return "Suggestion: Order or cook something she loves this week."
    if "dislike" in text:
        return "Suggestion: Keep this in mind when planning gifts or outings."
    return "Suggestion: Use this note when planning your next thoughtful moment together."


def remember(key: str, value: str) -> str:
    # Load existing notes and update the key if it already exists (case-insensitive).
    notes = load(GIRLFRIEND_FILE)
    key_to_match = key.strip().lower()

    for item in notes:
        if str(item.get("key", "")).strip().lower() == key_to_match:
            item["value"] = value
            save(GIRLFRIEND_FILE, notes)
            return f"Got it! I'll remember that {key} is {value}."

    # Add a new note when no existing key matches.
    notes.append({"key": key, "value": value})
    save(GIRLFRIEND_FILE, notes)
    return f"Got it! I'll remember that {key} is {value}."


def recall(key: str) -> str:
    # Find a saved note by key using case-insensitive matching.
    notes = load(GIRLFRIEND_FILE)
    key_to_match = key.strip().lower()

    for item in notes:
        if str(item.get("key", "")).strip().lower() == key_to_match:
            saved_key = str(item.get("key", key))
            saved_value = str(item.get("value", ""))
            suggestion = _suggestion_for_key(saved_key)
            return f"You told me {saved_key} is {saved_value}. {suggestion}"

    return f"I don't have anything saved for '{key}' yet."


def get_all() -> list:
    # Return all stored personal notes.
    return load(GIRLFRIEND_FILE)
