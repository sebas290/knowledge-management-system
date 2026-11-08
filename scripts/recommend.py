"""Component 2 - Recommend related documents by seed ID, query, and/or search history.

Examples:
  python scripts/recommend.py --id DOC001
  python scripts/recommend.py --query "my computer has a virus"
  python scripts/recommend.py --query "new phone" --history "VPN authentication error" --viewed DOC012
  python scripts/recommend.py --history "the printer is not working"      # recommended for you
"""
import argparse
import sys

from _common import load_system, table


def main():
    parser = argparse.ArgumentParser(description="Hybrid document recommender (TF-IDF + LSA + context)")
    parser.add_argument("--id", help="seed document ID (excluded from the results)")
    parser.add_argument("--query", help="free-text query")
    parser.add_argument("--history", nargs="*", default=[], help="previous queries, oldest first")
    parser.add_argument("--viewed", nargs="*", default=[], help="previously viewed document IDs")
    parser.add_argument("--k", type=int, default=5, help="number of recommendations (default 5)")
    args = parser.parse_args()

    from kms.context import SearchContext
    system = load_system()
    context = SearchContext()
    for q in args.history:
        context.add("search", q)
    for doc_id in args.viewed:
        context.add("view", doc_id.upper())

    try:
        results = system.recommender.recommend(doc_id=args.id, query=args.query,
                                               context=context if len(context) else None, k=args.k)
    except (KeyError, ValueError) as error:
        sys.exit(f"Error: {error.args[0] if error.args else error}")

    if args.id:
        seed = system.get(args.id)
        print(f"INPUT (ID): {seed.id} | {seed.category} | {seed.title}")
    if args.query:
        print(f"INPUT (TEXT): {args.query}")
    if len(context):
        print("SEARCH CONTEXT:", " -> ".join(f"{i.kind}:{i.value}" for i in context.items))
    rows = [r.as_row() for r in results]
    columns = ["ID", "Score", "Lexical (TF-IDF)", "Semantic (LSA)", "Context", "Category", "Title",
               "Shared terms", "Shared concepts"]
    if not len(context):
        columns.remove("Context")
    print(table(rows, columns))


if __name__ == "__main__":
    main()
