"""Document repository: loading, validation, and ontology-based concept detection."""
import csv
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from .text import normalize

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DEFAULT_CORPUS = DATA_DIR / "corpus.csv"
DEFAULT_ONTOLOGY = DATA_DIR / "ontology.json"
REQUIRED_COLUMNS = {"id", "title", "text"}


@dataclass
class Document:
    id: str
    title: str
    text: str
    category: str = "Uncategorized"
    source: str = "corpus"          # "corpus" or "user" (added from the interface)
    concepts: list[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return f"{self.title}. {self.text}"


def load_corpus(path=DEFAULT_CORPUS) -> list[Document]:
    """Read corpus.csv. Raises FileNotFoundError or ValueError with a clear message."""
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Corpus file not found: {path}")
    with open(path, encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"The corpus is missing the columns: {', '.join(sorted(missing))}")
        rows = list(reader)

    documents, seen = [], set()
    for number, row in enumerate(rows, start=2):
        doc_id = (row.get("id") or "").strip()
        text = (row.get("text") or "").strip()
        if not doc_id:
            raise ValueError(f"Row {number}: the document has no id.")
        if doc_id in seen:
            raise ValueError(f"Row {number}: the id '{doc_id}' is duplicated.")
        if not text:
            raise ValueError(f"Row {number} ({doc_id}): the text is empty.")
        seen.add(doc_id)
        documents.append(Document(
            id=doc_id,
            title=(row.get("title") or "").strip() or "(untitled)",
            text=text,
            category=(row.get("category") or "").strip() or "Uncategorized",
        ))
    if len(documents) < 4:
        raise ValueError("The corpus needs at least 4 documents.")
    return documents


class Ontology:
    """Concept lexicon, domains, and categories from data/ontology.json."""

    def __init__(self, path=DEFAULT_ONTOLOGY):
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Ontology file not found: {path}")
        self.raw = json.loads(path.read_text(encoding="utf-8"))
        self.concepts: dict[str, dict] = self.raw["concepts"]
        self.domains: dict[str, str] = self.raw["domains"]
        self.categories: dict[str, str] = self.raw["categories"]
        self.relations: dict[str, str] = self.raw["relations"]
        # One regex per concept; keywords match at the start of a word ("encrypt" -> "encrypted").
        self._patterns = {
            name: re.compile(r"\b(" + "|".join(re.escape(k) for k in info["keywords"]) + r")", re.I)
            for name, info in self.concepts.items()
        }

    def domain_of(self, concept: str) -> str:
        return self.concepts[concept]["domain"]

    def detect(self, text: str) -> list[str]:
        """Concepts whose keywords appear in the text."""
        text = normalize(text)
        return [name for name, pattern in self._patterns.items() if pattern.search(text)]

    def matched_keywords(self, text: str, concept: str) -> list[str]:
        text = normalize(text)
        return sorted({m.group(1).lower() for m in self._patterns[concept].finditer(text)})
