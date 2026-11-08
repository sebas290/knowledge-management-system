"""Shared helpers for the command-line scripts."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVIDENCE_DIR = ROOT / "evidence"


def load_system():
    from kms.system import KnowledgeSystem
    try:
        return KnowledgeSystem()
    except (FileNotFoundError, ValueError) as error:
        sys.exit(f"Error loading the repository: {error}")


def table(rows: list[dict], columns: list[str] | None = None) -> str:
    """Plain-text table for console output."""
    if not rows:
        return "(no results)"
    columns = columns or list(rows[0])
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in columns}
    line = "  ".join(c.ljust(widths[c]) for c in columns)
    sep = "  ".join("-" * widths[c] for c in columns)
    body = ["  ".join(str(r.get(c, "")).ljust(widths[c]) for c in columns) for r in rows]
    return "\n".join([line, sep, *body])
