FORBIDDEN_PATTERNS = [
    "ignore previous instructions",
    "reveal system prompt",
    "show hidden prompt",
    "print system prompt",
    "show all data",
    "get all data",
    "dump database"
]

def is_prompt_injection(text):
    text = text.lower()
    return any(pattern in text for pattern in FORBIDDEN_PATTERNS)
