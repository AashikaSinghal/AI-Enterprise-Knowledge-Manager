import os
from agents import function_tool

DATA_DIR = "data"

@function_tool
def list_documents() -> list[str]:
    """Return the names of every document available in the knowledge base."""
    return os.listdir(DATA_DIR)

@function_tool
def read_document(filename: str) -> str:
    """Return the full text content of one document by filename."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        return f"Error: {filename} not found."
    with open(path, "r") as f:
        return f.read()

@function_tool
def search_documents(query: str) -> str:
    """Search all documents for lines containing the query text, return matches with source filenames."""
    results = []
    for fname in os.listdir(DATA_DIR):
        with open(os.path.join(DATA_DIR, fname)) as f:
            for line in f:
                if query.lower() in line.lower():
                    results.append(f"[{fname}] {line.strip()}")
    return "\n".join(results) if results else "No matches found."

@function_tool
def log_meeting_note(note: str) -> str:
    """Append a new meeting note to the meeting notes file."""
    with open(os.path.join(DATA_DIR, "meeting_notes.txt"), "a") as f:
        f.write(note + "\n")
    return "Note saved."

@function_tool(needs_approval=True)
def flag_policy_update(document: str, proposed_change: str) -> str:
    """Propose a change to a knowledge-base document. Requires human approval before it is applied."""
    with open(os.path.join(DATA_DIR, document), "a") as f:
        f.write(f"\n[PENDING UPDATE] {proposed_change}\n")
    return f"Update proposed for {document} and applied after approval."
