# AI Enterprise Knowledge Manager
### Capstone Project — Deliverables 1 & 2: Problem Analysis and Multi-Agent Design

---

## 1. Problem Analysis

### 1.1 Business Context

Employees at most organizations waste significant time searching across scattered
sources — handbooks, IT policy documents, and meeting notes — to answer routine
questions ("How many leave days do I get?", "Is VPN required for remote work?",
"What did we decide in last week's standup?"). This information usually exists
somewhere, but it is unstructured, spread across files, and not searchable in
natural language. Employees either interrupt colleagues/managers for answers
already documented, or give up and make assumptions — both of which cost time
and introduce inconsistency.

### 1.2 Stakeholders

| Stakeholder | Interest |
|---|---|
| Employees | Need fast, accurate answers to policy/handbook/meeting questions without hunting through files |
| HR / IT Administrators | Own the source documents (handbook, IT policy) and need control over what gets changed and how |
| Team Leads / Managers | Rely on meeting notes being captured and retrievable later |
| Knowledge/Compliance Owner | Needs assurance that no document is silently altered without a human sign-off |

### 1.3 Problem Statement

Build a multi-agent system that lets an employee ask natural-language questions
against a company's internal knowledge base (handbook, IT policy, meeting notes)
and receive an accurate, cited answer — while also allowing the system to
**flag outdated or missing information** and propose updates, subject to
**mandatory human approval** before any document is modified.

### 1.4 Objectives

1. Answer employee questions accurately by routing them to the right knowledge
   domain (general handbook, IT/security policy, or meeting history).
2. Cite the exact source document for every answer, so trust is verifiable.
3. Allow the system to log new meeting notes as they happen, growing the
   knowledge base over time.
4. Detect when an answer implies a document is outdated or incomplete, and
   propose a specific fix — but never apply that fix without a human approving it.
5. Maintain conversational memory across a session, so follow-up questions
   don't require repeating context.
6. Return every final answer in a strict, machine-readable structured format
   (not free text), so the system could plug into a dashboard or ticketing tool later.

---

## 2. Multi-Agent Design

### 2.1 Agent Architecture

The system uses a **triage-and-specialist** pattern: one entry-point agent
inspects the employee's question and hands off to whichever specialist agent
is equipped to answer it. Specialist outputs are then normalized by a
Recommendation agent into a single structured answer, and a Curator agent
checks whether anything in that answer suggests the knowledge base itself
needs updating.

```
Employee question
      │
      ▼
┌─────────────────────┐
│  Knowledge Search    │  (triage / router)
└──────────┬───────────┘
           │  hands off to one of:
   ┌───────┼────────────┐
   ▼       ▼             ▼
┌────────┐ ┌───────────┐ ┌───────────────┐
│Document│ │  Policy   │ │    Meeting    │
│ Reader │ │  Expert   │ │    Memory     │
└───┬────┘ └─────┬─────┘ └───────┬───────┘
    └─────────────┼───────────────┘
                   ▼
        ┌────────────────────┐
        │ Recommendation      │  → structured KnowledgeAnswer
        │ Agent                │     (answer, source_documents, confidence)
        └──────────┬───────────┘
                   ▼
        ┌────────────────────┐
        │ Knowledge Curator    │  → structured CuratorFlag
        │ (flags outdated info)│     (issue_found, reasoning, proposed_update)
        └──────────┬───────────┘
                   ▼
        ⏸ Human approval required
        before flag_policy_update
        actually writes to a file
```

### 2.2 Roles of Each Agent

| Agent | Role |
|---|---|
| **Knowledge Search** | Front door. Reads the raw question and hands off to the correct specialist based on topic (named document, policy question, or meeting/decision-related). Answers trivial questions itself if no handoff is needed. |
| **Document Reader** | Returns the exact, verbatim content of a specific named document when the employee asks about "the handbook" or a specific file. |
| **Policy Expert** | Searches across all documents for policy-relevant lines (HR/IT) and answers with the specific matching text, cited by filename. |
| **Meeting Memory** | Logs new meeting notes as they're shared, and recalls past ones via search when asked "what did we decide about X." |
| **Recommendation Agent** | Takes whatever the specialist produced and turns it into the final, strict structured output (`KnowledgeAnswer`) — answer text, list of source documents, and a confidence rating. |
| **Knowledge Curator** | Reviews the final answer for signs that a document is outdated, missing, or wrong. If so, it proposes a specific edit via the `flag_policy_update` tool — which is gated behind human approval. |

### 2.3 Agent Interaction and Handoff Flow

1. Employee sends a question to **Knowledge Search**.
2. Knowledge Search's instructions route it via an SDK `handoff` to exactly one
   of: **Document Reader**, **Policy Expert**, or **Meeting Memory** — chosen
   by keyword/intent (document name → Reader, policy language → Expert,
   meeting/decision language → Memory).
3. The specialist agent uses its tools (see 2.4) to retrieve the answer and
   returns free-text output back up the chain.
4. That output is passed into **Recommendation Agent**, which is constrained
   by `output_type=KnowledgeAnswer` (a Pydantic schema) — so its response is
   guaranteed to be valid structured JSON, not prose.
5. The structured answer's text is passed into **Knowledge Curator**
   (`output_type=CuratorFlag`), which decides whether the answer implies a
   document should be updated.
6. If Curator decides yes, it calls the `flag_policy_update` tool. That tool
   is marked `needs_approval=True`, so the SDK run **pauses and returns an
   interruption** instead of executing the write.
7. `main.py` detects the interruption, prompts a human (`Approve? (y/n)`),
   and only resumes/executes the file write if approved — otherwise the
   proposed change is discarded.
8. All of this happens inside one `SQLiteSession`, so context (e.g., a
   follow-up "what about remote work?") persists across turns without the
   employee repeating themselves.

### 2.4 Tool Integration Overview

| Tool | Used by | Purpose | Needs Approval? |
|---|---|---|---|
| `list_documents` | Knowledge Search, Document Reader | Lists all files in the knowledge base | No |
| `read_document` | Document Reader, Policy Expert | Returns full text of one named file | No |
| `search_documents` | Policy Expert, Meeting Memory | Full-text search across all files, returns matching lines with source filename | No |
| `log_meeting_note` | Meeting Memory | Appends a new note to `meeting_notes.txt` | No |
| `flag_policy_update` | Knowledge Curator | Proposes and (once approved) writes a change into a knowledge-base document | **Yes** — gated by human approval |

### 2.5 Memory / Context Management

A single `SQLiteSession`, keyed per employee (`"employee_1"`), is passed into
every `Runner.run()` call for that conversation. This means the model sees the
full prior exchange on each new question, enabling natural follow-ups without
the employee re-stating context.

### 2.6 Human Approval Workflow

The `flag_policy_update` tool is the only tool in the system capable of
mutating a source document, and it is explicitly marked `needs_approval=True`.
When the Curator agent calls it, the SDK returns an `interruption` instead of
executing the tool. `main.py` surfaces this to a human operator, who approves
or rejects it; only on approval does the underlying file actually change. This
guarantees no knowledge-base document is ever silently altered by the AI.

---

*This document maps directly to Deliverables 1 and 2 of the capstone brief.
The architecture described above matches the actual working implementation in
`schemas.py`, `tools.py`, `agents_setup.py`, and `main.py`, and has been
tested end-to-end including a live human-approval cycle.*
