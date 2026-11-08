"""Component 3 - Chatbot over the document repository.

Examples:
  python scripts/chatbot.py                                   # interactive session
  python scripts/chatbot.py --ask "How do I reset my password?" "and what if my account is locked?"
"""
import argparse

from _common import load_system


def show(response) -> None:
    print(f"\nYOU: {response.question}")
    print(f"BOT: {response.answer.replace('**', '')}")
    if response.sources:
        print(f"     [intent: {response.intent} | retrieval query: {response.retrieval_query!r}]")
        for s in response.sources:
            print(f"     source {s.document.id} score={s.score:.3f}  {s.document.title}")


def main():
    parser = argparse.ArgumentParser(description="Knowledge base chatbot")
    parser.add_argument("--ask", nargs="+", help="one or more questions, asked in order (keeps follow-up context)")
    args = parser.parse_args()
    bot = load_system().chatbot

    if args.ask:
        for question in args.ask:
            show(bot.ask(question))
        return
    print("Altavista knowledge assistant. Type 'exit' to quit, 'reset' to forget the conversation.")
    while True:
        try:
            question = input("\nYOU: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if question.lower() in {"exit", "quit"}:
            break
        if question.lower() == "reset":
            bot.reset()
            print("Conversation context cleared.")
            continue
        show(bot.ask(question))


if __name__ == "__main__":
    main()
