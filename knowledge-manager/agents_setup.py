import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, OpenAIChatCompletionsModel
from tools import list_documents, read_document, search_documents, log_meeting_note, flag_policy_update
from schemas import KnowledgeAnswer, CuratorFlag

load_dotenv()

gemini_client = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

def gemini_model():
    # Use gemini-3.5-flash-lite while testing (higher free daily quota).
    # Switch to gemini-3.6-flash for your final demo recording if you want higher quality.
    return OpenAIChatCompletionsModel(model="gemini-3.5-flash-lite", openai_client=gemini_client)

document_reader = Agent(
    name="Document Reader",
    handoff_description="Reads and returns the exact content of a named document.",
    instructions="Use list_documents and read_document to answer what a specific document says.",
    tools=[list_documents, read_document],
    model=gemini_model(),
)

policy_expert = Agent(
    name="Policy Expert",
    handoff_description="Answers HR and IT policy questions with citations.",
    instructions="Use search_documents to find the relevant policy text and answer clearly, citing the source file.",
    tools=[search_documents, read_document],
    model=gemini_model(),
)

meeting_memory = Agent(
    name="Meeting Memory",
    handoff_description="Stores new meeting notes and recalls past ones.",
    instructions="If the user is sharing something that was decided/discussed, call log_meeting_note. If they're asking about a past decision, use search_documents.",
    tools=[log_meeting_note, search_documents],
    model=gemini_model(),
)

recommendation_agent = Agent(
    name="Recommendation Agent",
    handoff_description="Produces the final structured, cited answer.",
    instructions="Answer only the user's most recent question directly and concisely. Ignore earlier unrelated topics from the conversation history. Always cite the source document(s).",
    output_type=KnowledgeAnswer,
    model=gemini_model(),
)

knowledge_curator = Agent(
    name="Knowledge Curator",
    handoff_description="Checks if the knowledge base looks outdated and proposes fixes.",
    instructions="Decide if the answer given suggests a document is missing or outdated. If so, call flag_policy_update with a specific proposed change. If not, set issue_found to false.",
    tools=[flag_policy_update],
    output_type=CuratorFlag,
    model=gemini_model(),
)

knowledge_search = Agent(
    name="Knowledge Search",
    instructions=(
        "You are the front door for employee questions. "
        "If the question names a specific document, hand off to Document Reader. "
        "If it's about HR/IT policy, hand off to Policy Expert. "
        "If it's about meetings/decisions, hand off to Meeting Memory. "
        "Otherwise answer briefly yourself."
    ),
    handoffs=[document_reader, policy_expert, meeting_memory],
    tools=[list_documents],
    model=gemini_model(),
)
