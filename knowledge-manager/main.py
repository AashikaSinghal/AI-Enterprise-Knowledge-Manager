import asyncio
from agents import Runner, SQLiteSession
from agents_setup import knowledge_search, recommendation_agent, knowledge_curator

async def main():
    session = SQLiteSession("employee_1")

    print("Knowledge Manager ready. Type 'quit' to exit.\n")
    while True:
        question = input("You: ")
        if question.lower() == "quit":
            break

        result = await Runner.run(knowledge_search, question, session=session)
        print(f"\n[{result.last_agent.name} answered]")
        print(result.final_output)

        final = await Runner.run(recommendation_agent, result.final_output, session=session)
        print("\nFinal structured answer:")
        print(final.final_output.model_dump_json(indent=2))

        curated = await Runner.run(knowledge_curator, final.final_output.answer, session=session)

        if curated.interruptions:
            for item in curated.interruptions:
                print(f"\nApproval needed: {item.tool_name} wants to change a document.")
                decision = input("Approve? (y/n): ")
                state = curated.to_state()
                if decision.lower() == "y":
                    state.approve(item)
                else:
                    state.reject(item)
                curated = await Runner.run(knowledge_curator, state)
                print(f"\n[Update applied] {curated.final_output.proposed_update}")

        print()

if __name__ == "__main__":
    asyncio.run(main())
