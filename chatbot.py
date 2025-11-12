from __future__ import annotations
import asyncio
from dotenv import load_dotenv
from pydantic_ai import Agent

# Load environment variables from .env
load_dotenv(override=True)

# Pick a model; default to Gemini flash. Change if needed.
MODEL = "google-gla:gemini-2.5-flash"  # e.g. "openai:gpt-4o-mini"
agent = Agent(MODEL)

EXIT = {"exit", "quit", "bye"}

async def main():
    history = []  # simple in-memory chat context
    while True:
        user = input("You: ")
        if user.strip().lower() in EXIT:
            break
        if not user.strip():
            continue
        try:
            result = await agent.run(user, message_history=history)
        except Exception as e:
            print("(error)", e)
            continue
        print("Agent:", result.output)
        history = result.all_messages()
    print("Goodbye!")

if __name__ == "__main__":
    asyncio.run(main())
