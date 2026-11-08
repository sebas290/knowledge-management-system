"""Component 4 - Knowledge graph built from the ontology and the system data (NetworkX + PyVis).

Node types: Document, Category, Concept, Domain.
Edge relations: belongs_to, mentions, part_of, related_to, similar_to, governed_by
(definitions in data/ontology.json).
"""
import json
import re
from collections import Counter
from itertools import combinations

import networkx as nx
import numpy as np

STYLE = {  # node type -> (color, shape, size)
    "Document": ("#4C78A8", "dot", 12),
    "Category": ("#E45756", "diamond", 26),
    "Concept": ("#54A24B", "triangle", 16),
    "Domain": ("#F58518", "star", 28),
}
EDGE_COLOR = {
    "belongs_to": "#E45756", "mentions": "#9ecf8f", "part_of": "#F58518",
    "related_to": "#54A24B", "similar_to": "#4C78A8", "governed_by": "#B279A2",
}
CATEGORY_COLOR = {"Policy/Process": "#4C78A8", "Support/Incidents": "#72B7B2", "FAQ": "#EECA3B", "Minutes": "#9D755D"}


def build_graph(documents, ontology, similarity: np.ndarray, similar_threshold: float = 0.35,
                governed_threshold: float = 0.15, cooccurrence_min: int = 3) -> nx.Graph:
    g = nx.Graph()
    for domain, desc in ontology.domains.items():
        g.add_node(f"domain:{domain}", label=domain, type="Domain", info=desc)
    for category, desc in ontology.categories.items():
        g.add_node(f"cat:{category}", label=category, type="Category", info=desc)
    for concept, info in ontology.concepts.items():
        g.add_node(f"concept:{concept}", label=concept, type="Concept", info=f"Domain: {info['domain']}")
        g.add_edge(f"concept:{concept}", f"domain:{info['domain']}", relation="part_of")

    for d in documents:
        cat_node = f"cat:{d.category}"
        if cat_node not in g:
            g.add_node(cat_node, label=d.category, type="Category", info="Category added by the user")
        g.add_node(d.id, label=d.id, type="Document", category=d.category, source=d.source,
                   info=f"{d.title} | {d.category}" + (" | added by user" if d.source == "user" else ""))
        g.add_edge(d.id, cat_node, relation="belongs_to")
        for concept in d.concepts:
            g.add_edge(d.id, f"concept:{concept}", relation="mentions")

    # Concept co-occurrence
    pairs = Counter()
    for d in documents:
        pairs.update(combinations(sorted(d.concepts), 2))
    for (a, b), n in pairs.items():
        if n >= cooccurrence_min:
            g.add_edge(f"concept:{a}", f"concept:{b}", relation="related_to", weight=n)

    # Document similarity and governance
    n = len(documents)
    for i in range(n):
        for j in range(i + 1, n):
            if similarity[i, j] >= similar_threshold:
                g.add_edge(documents[i].id, documents[j].id, relation="similar_to", weight=float(similarity[i, j]))
    policies = [i for i, d in enumerate(documents) if d.category == "Policy/Process"]
    for i, d in enumerate(documents):
        if d.category == "Policy/Process" or not policies:
            continue
        candidates = [j for j in policies if set(d.concepts) & set(documents[j].concepts)]
        if not candidates:
            continue
        best = max(candidates, key=lambda j: similarity[i, j])
        if similarity[i, best] >= governed_threshold and not g.has_edge(d.id, documents[best].id):
            g.add_edge(d.id, documents[best].id, relation="governed_by", weight=float(similarity[i, best]))
    return g


def filter_graph(g: nx.Graph, node_types=None, relations=None, focus: str | None = None, radius: int = 1) -> nx.Graph:
    """Subgraph with the selected node types/relations, optionally around one node."""
    node_types = set(node_types or STYLE)
    relations = set(relations or EDGE_COLOR)
    h = nx.Graph()
    h.add_nodes_from((n, a) for n, a in g.nodes(data=True) if a["type"] in node_types)
    h.add_edges_from((u, v, a) for u, v, a in g.edges(data=True)
                     if a["relation"] in relations and u in h and v in h)
    if focus and focus in h:
        h = nx.ego_graph(h, focus, radius=radius)
    return h


def graph_summary(g: nx.Graph) -> dict:
    types = Counter(a["type"] for _, a in g.nodes(data=True))
    relations = Counter(a["relation"] for _, _, a in g.edges(data=True))
    concept_degree = sorted(((a["label"], g.degree(n)) for n, a in g.nodes(data=True) if a["type"] == "Concept"),
                            key=lambda x: -x[1])
    return {"nodes": dict(types), "edges": dict(relations), "top_concepts": concept_degree[:10]}


def to_pyvis_html(g: nx.Graph, highlight: set[str] | None = None, height: str = "640px") -> str:
    """Interactive HTML (drag, zoom, hover tooltips) for Streamlit or a standalone file."""
    from pyvis.network import Network

    highlight = highlight or set()
    net = Network(height=height, width="100%", bgcolor="#ffffff", font_color="#222222",
                  cdn_resources="in_line", notebook=False)
    for node, a in g.nodes(data=True):
        color, shape, size = STYLE[a["type"]]
        if a["type"] == "Document":
            color = CATEGORY_COLOR.get(a.get("category"), color)
        border = 4 if node in highlight else 1
        # vis-network 9 renders string labels and tooltips as plain text (no HTML injection).
        net.add_node(node, label=a["label"], title=f"{a['type']}: {a.get('info', a['label'])}",
                     color={"background": color, "border": "#d62728" if node in highlight else color},
                     shape=shape, size=size * (1.5 if node in highlight else 1), borderWidth=border)
    for u, v, a in g.edges(data=True):
        title = a["relation"] + (f" ({a['weight']:.2f})" if isinstance(a.get("weight"), float) else "")
        net.add_edge(u, v, title=title, color=EDGE_COLOR[a["relation"]],
                     dashes=a["relation"] == "governed_by", width=2 if a["relation"] == "similar_to" else 1)
    big = g.number_of_nodes() > 40
    net.set_options(json.dumps({
        "physics": {"solver": "forceAtlas2Based",
                    "forceAtlas2Based": {"gravitationalConstant": -120 if big else -60, "centralGravity": 0.015,
                                         "springLength": 120 if big else 90, "avoidOverlap": 0.4},
                    "stabilization": {"enabled": True, "iterations": 400, "fit": True},
                    "minVelocity": 1.0},
        "edges": {"smooth": False, "color": {"opacity": 0.45 if big else 0.8}},
        "nodes": {"font": {"size": 12 if big else 14}},
        "interaction": {"hover": True, "navigationButtons": True, "tooltipDelay": 120, "hideEdgesOnDrag": big},
    }))
    html = net.generate_html()
    # vis-network is embedded inline (works offline and in Streamlit Cloud); drop the template's
    # unused external references (local node_modules paths and Bootstrap, not needed here).
    html = re.sub(r'<(script|link)[^>]+(node_modules|bootstrap)[^>]*>(</script>)?', "", html)
    # Fit the whole graph in view when the layout settles and whenever the frame is resized
    # (a graph drawn inside a hidden Streamlit tab gets its real size only when the tab opens).
    fit = ("<script>if (typeof network !== 'undefined') {"
           "network.once('stabilizationIterationsDone', function () { network.fit(); });"
           "window.addEventListener('resize', function () { network.fit(); });"
           "setTimeout(function () { network.fit(); }, 3000);}</script>")
    return html.replace("</body>", fit + "</body>")
