"""Text preprocessing shared by every component (reused and extended from Activity 3)."""
import re
import unicodedata

# Common English stopwords (removed during text cleaning).
STOPWORDS_EN = {
    "a", "about", "after", "all", "also", "am", "an", "and", "any", "are", "as", "at",
    "be", "because", "been", "before", "but", "by", "can", "could", "did", "do",
    "does", "for", "from", "had", "has", "have", "he", "her", "his", "how", "i", "if",
    "in", "into", "is", "it", "its", "me", "may", "must", "my", "no", "not", "of",
    "on", "once", "only", "or", "other", "our", "she", "so", "such", "than",
    "that", "the", "their", "them", "then", "there", "these", "they", "this",
    "to", "up", "was", "we", "were", "what", "when", "where", "which", "who", "why",
    "will", "with", "within", "without", "would", "you", "your", "should", "being",
    "each", "every", "one", "two", "get", "got", "need", "want", "please", "hi",
    "hello", "thanks", "thank", "know", "tell", "let", "us", "there",
}

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9])")


def simple_stem(token: str) -> str:
    """Light stemming so that 'passwords'/'password' or 'changing'/'changed' match."""
    if len(token) > 4 and token.endswith("ies"):
        token = token[:-3] + "y"
    elif token.endswith("sses"):
        token = token[:-2]
    elif len(token) > 3 and token.endswith("s") and not token.endswith(("ss", "us", "is")):
        token = token[:-1]
    if len(token) > 5 and token.endswith("ing"):
        token = token[:-3]
    elif len(token) > 4 and token.endswith("ed"):
        token = token[:-2]
    if len(token) > 4 and token.endswith("e"):
        token = token[:-1]
    return token


def normalize(text: str) -> str:
    """Lowercase and remove accents."""
    text = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))


# Synonym and phrase normalization (addresses the synonym/ambiguity limitation found in
# Activity 3: "log in" was confused with "log files"). Applied to documents and queries alike.
SYNONYMS = [
    (r"\b(log\s?in|log\s?on|sign\s?in|signin)\b", " signin "),
    (r"\b(can\s?not|can't|cant|unable to)\b", " unable "),
    (r"\be-?mails?\b", " email "),
    (r"\b(wi-?fi|wlan)\b", " wireless "),
    (r"\b(viruses|virus|trojan|ransomware)\b", " malware "),
    (r"\b(pc|workstation)\b", " computer "),
    (r"\b(2fa|mfa|two-factor|multi-factor)\b", " mfa "),
    (r"\b(cell\s?phone|smartphone|mobile phone)\b", " phone "),
    (r"\bprograms?\b", " software "),
    (r"\b(work|working) from home\b", " remote home "),
    (r"\bremotely\b", " remote "),
]
_SYNONYMS = [(re.compile(p), r) for p, r in SYNONYMS]


USE_SYNONYMS = True  # switched off only by the evaluation, to measure the Activity 3 baseline


def apply_synonyms(text: str) -> str:
    if not USE_SYNONYMS:
        return text
    for pattern, replacement in _SYNONYMS:
        text = pattern.sub(replacement, text)
    return text


def clean_text(text: str) -> str:
    """Lowercase, no accents, synonym normalization, no symbols or stopwords, light stemming."""
    text = re.sub(r"[^a-z0-9\s]", " ", apply_synonyms(normalize(text)))
    tokens = [simple_stem(t) for t in text.split() if len(t) >= 2 and t not in STOPWORDS_EN]
    return " ".join(tokens)


def split_sentences(text: str) -> list[str]:
    """Split a document into sentences (used by the chatbot to build answers)."""
    return [s.strip() for s in _SENTENCE_SPLIT.split(text or "") if s.strip()]
