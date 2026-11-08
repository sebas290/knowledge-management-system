"""Search context: the query history shared by the search box, the chatbot, and document views."""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Interaction:
    kind: str        # "search", "chat", or "view"
    value: str       # the query text, or the document id for a view
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%H:%M:%S"))


class SearchContext:
    """Keeps the last interactions of a user session.

    Recent interactions weigh more: weight = decay ** age (age 0 = most recent).
    """

    def __init__(self, max_items: int = 10, decay: float = 0.6):
        self.max_items = max_items
        self.decay = decay
        self.items: list[Interaction] = []

    def add(self, kind: str, value: str) -> None:
        value = (value or "").strip()
        if not value:
            return
        if self.items and self.items[-1].kind == kind and self.items[-1].value == value:
            return  # avoid duplicating the same consecutive action
        self.items.append(Interaction(kind, value))
        self.items = self.items[-self.max_items:]

    def weighted(self) -> list[tuple[Interaction, float]]:
        n = len(self.items)
        return [(item, self.decay ** (n - 1 - i)) for i, item in enumerate(self.items)]

    def viewed_ids(self) -> set[str]:
        return {i.value for i in self.items if i.kind == "view"}

    def clear(self) -> None:
        self.items.clear()

    def __len__(self) -> int:
        return len(self.items)
