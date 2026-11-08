"""Component 4 - Build the knowledge graph and export it as interactive HTML, GraphML, or JSON.

Examples:
  python scripts/build_graph.py                               # evidence/knowledge_graph.html
  python scripts/build_graph.py --focus DOC012 --radius 2 --out evidence/graph_DOC012.html
  python scripts/build_graph.py --graphml evidence/knowledge_graph.graphml
"""
import argparse
import json
import sys
from pathlib import Path

import networkx as nx

from _common import EVIDENCE_DIR, load_system


def main():
    parser = argparse.ArgumentParser(description="Knowledge graph (NetworkX + PyVis)")
    parser.add_argument("--out", default=str(EVIDENCE_DIR / "knowledge_graph.html"), help="HTML output path")
    parser.add_argument("--focus", help="node to center on: a document ID, 'concept:<name>', or 'cat:<name>'")
    parser.add_argument("--radius", type=int, default=1, help="hops around --focus (default 1)")
    parser.add_argument("--graphml", help="also export GraphML (opens in Gephi or yEd)")
    parser.add_argument("--json", help="also export node-link JSON")
    args = parser.parse_args()

    from kms.graph import filter_graph, graph_summary, to_pyvis_html
    system = load_system()
    g = system.graph
    if args.focus:
        focus = args.focus.upper() if args.focus.lower().startswith("doc") else args.focus
        if focus not in g:
            sys.exit(f"Error: the node '{args.focus}' is not in the graph.")
        g = filter_graph(g, focus=focus, radius=args.radius)

    summary = graph_summary(g)
    print("Nodes:", summary["nodes"])
    print("Edges:", summary["edges"])
    print("Most connected concepts:", ", ".join(f"{c} ({d})" for c, d in summary["top_concepts"][:5]))

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(to_pyvis_html(g, highlight={args.focus.upper()} if args.focus else None), encoding="utf-8")
    print(f"Interactive graph saved to {out}")
    if args.graphml:
        nx.write_graphml(g, args.graphml)
        print(f"GraphML saved to {args.graphml}")
    if args.json:
        Path(args.json).write_text(json.dumps(nx.node_link_data(g, edges="links"), indent=1), encoding="utf-8")
        print(f"JSON saved to {args.json}")


if __name__ == "__main__":
    main()
