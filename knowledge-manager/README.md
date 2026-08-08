# AI Enterprise Knowledge Manager

A multi-agent AI system built with the **OpenAI Agents SDK** (running on
**Google Gemini** via its OpenAI-compatible endpoint) that answers employee
questions from a company's internal knowledge base — with citations, session
memory, structured output, and a human-approval gate before any document is
ever changed.

Capstone project — Summer School '26, OpenAI Agents SDK track.

---

## What it does

Ask it things like:

- "What does the IT policy say about VPN access?"
- "Log a meeting note: Jan 20 standup, we decided to skip Friday deploys."
- "The password reset rule is outdated, it should be 60 days not 90 — please update it."

It routes your question to the right specialist agent, answers with the exact
source document, and — if it detects a document might need updating — proposes
a specific change and **pauses for a human to approve or reject it** before
touching any file.

---

## Architecture

See [`architecture_diagram.mermaid`](./architecture_diagram.mermaid) for the
full visual flow. In short:

```
Employee question
      │
      ▼
Knowledge Search (triage)
      │
      ├── Document Reader   (named-document lookups)
      ├── Policy Expert     (HR / IT policy questions)
      └── Meeting Memory    (logging + recalling meeting notes)
              │
              ▼
     Recommendation Agent  →  structured KnowledgeAnswer
              │
              ▼
      Knowledge Curator     →  structured CuratorFlag
              │
              ▼
   ⏸ Human approval required
   before flag_policy_update
   writes to a real file
```

## Agents

| Agent | Responsibility |
|---|---|
| Knowledge Search | Routes each question to the right specialist via handoff |
| Document Reader | Returns exact content of a named document |
| Policy Expert | Searches all documents, answers policy questions with citations |
| Meeting Memory | Logs new meeting notes and recalls past ones |
| Recommendation Agent | Produces the final structured, cited answer |
| Knowledge Curator | Flags outdated/missing info and proposes fixes (human-gated) |

## Tools

| Tool | Purpose | Approval needed? |
|---|---|---|
| `list_documents` | Lists all files in the knowledge base | No |
| `read_document` | Reads one file's full content | No |
| `search_documents` | Full-text search across all files | No |
| `log_meeting_note` | Appends a new meeting note | No |
| `flag_policy_update` | Proposes + applies a document change | **Yes** |

---

## Tech stack

- Python 3.14
- [`openai-agents`](https://pypi.org/project/openai-agents/) SDK — agents, handoffs, tools, structured outputs, human-approval interruptions
- Google Gemini (`gemini-3.6-flash` / `gemini-3.5-flash-lite`) via Gemini's OpenAI-compatible endpoint
- `pydantic` for structured output schemas
- `SQLiteSession` for conversation memory
- Plain `.txt` files as the knowledge base (`data/`)

---

## Project structure

```
knowledge-manager/
├── .env                  # GEMINI_API_KEY (not committed)
├── data/
│   ├── handbook.txt
│   ├── it_policy.txt
│   └── meeting_notes.txt
├── schemas.py             # Pydantic structured-output models
├── tools.py                # 5 function_tools
├── agents_setup.py         # 6 agents, handoffs, Gemini model config
└── main.py                  # Chat loop, session memory, approval workflow
```

---

## Setup

```powershell
git clone <your-repo-url>
cd knowledge-manager
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install openai-agents python-dotenv
```

Create a `.env` file:

```
GEMINI_API_KEY=your-real-gemini-key-here
```

Get a free key from [Google AI Studio](https://aistudio.google.com/).

## Run

```powershell
python main.py
```

Type a question at the `You:` prompt. Type `quit` to exit.

---

## Example session

```
You: What does the IT policy say about VPN access?

[Policy Expert answered]
According to the IT policy, VPN is required for all remote access to company systems.

Final structured answer:
{
  "answer": "The IT policy states that VPN is required for all remote access to company systems.",
  "source_documents": ["it_policy.txt"],
  "confidence": "high"
}
```

---

## Human approval in action

When the Knowledge Curator proposes a document change, the program pauses:

```
Approval needed: flag_policy_update wants to change a document.
Approve? (y/n): y
```

Only on `y` does the underlying `.txt` file actually get modified — the AI
never edits company documents unsupervised.

---

## Known limitations / free-tier notes

- Gemini's free tier has a daily request quota per model. If you hit a
  `RESOURCE_EXHAUSTED` / 429 error, switch the model name in
  `agents_setup.py` to `gemini-3.5-flash-lite`, which has a higher free cap.
- This is a demo knowledge base using local `.txt` files — a production
  version would connect to a real document store (SharePoint, Confluence,
  Google Drive, etc.) instead.

---

## Author

Built as a capstone project for the OpenAI Agents SDK Summer School '26 track, IIT Jammu.
