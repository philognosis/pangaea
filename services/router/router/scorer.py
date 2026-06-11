"""
Keyword-based intent scorer with in-memory hot-path cache.

Phase 1 router — P6: compiled paths are the performance contract.
Second call for same utterance uses cache (no model invoked).
"""
import hashlib
import re
from .models import RouteResult, ClarificationNeeded

MIN_CONFIDENCE = 0.85


def _utterance_hash(utterance: str) -> str:
    return hashlib.sha256(utterance.lower().strip().encode()).hexdigest()


def _strip_slots(template: str) -> str:
    return re.sub(r"\{[^}]+\}", "", template).strip()


def _score_utterance(utterance: str, template: str) -> float:
    utterance_lower = utterance.lower().strip()
    template_clean = _strip_slots(template).lower()

    if template_clean == utterance_lower:
        return 1.0

    # Check if utterance starts with the template keywords
    if template_clean and utterance_lower.startswith(template_clean):
        return 0.95

    template_words = set(template_clean.split()) - {"", "for", "the", "a", "an", "my"}
    utterance_words = set(utterance_lower.split())
    if not template_words:
        return 0.0
    overlap = template_words & utterance_words
    return len(overlap) / len(template_words)


class Router:
    def __init__(self):
        self._capabilities: list[dict] = []
        self._hot_paths: dict[str, RouteResult] = {}

    def reset(self):
        self._capabilities.clear()
        self._hot_paths.clear()

    def register_capability(self, capability_id: str, intents: list[dict]) -> None:
        self._capabilities = [c for c in self._capabilities if c["capability_id"] != capability_id]
        self._capabilities.append({"capability_id": capability_id, "intents": intents})

    def is_hot_path(self, utterance: str) -> bool:
        return _utterance_hash(utterance) in self._hot_paths

    def route(self, utterance: str) -> RouteResult | ClarificationNeeded:
        key = _utterance_hash(utterance)

        # Check compiled hot path first (P6)
        if key in self._hot_paths:
            result = self._hot_paths[key]
            return RouteResult(
                capability_id=result.capability_id,
                intent_id=result.intent_id,
                confidence=result.confidence,
                slots=result.slots,
                compiled=True,
            )

        best_score = 0.0
        best_cap = None
        best_intent = None

        for cap in self._capabilities:
            for intent in cap["intents"]:
                for template in intent.get("utterances", []):
                    score = _score_utterance(utterance, template)
                    if score > best_score:
                        best_score = score
                        best_cap = cap["capability_id"]
                        best_intent = intent["id"]

        if best_score >= MIN_CONFIDENCE and best_cap and best_intent:
            result = RouteResult(
                capability_id=best_cap,
                intent_id=best_intent,
                confidence=best_score,
                compiled=False,
            )
            # Compile to hot path
            self._hot_paths[key] = result
            return result

        partial = [
            f"{cap['capability_id']}.{intent['id']}"
            for cap in self._capabilities
            for intent in cap["intents"]
            for tmpl in intent.get("utterances", [])
            if _score_utterance(utterance, tmpl) > 0.3
        ][:3]

        return ClarificationNeeded(
            question="I'm not sure what you'd like to do. Could you be more specific?",
            partial_matches=partial,
        )
