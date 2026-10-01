from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Tuple


STOPWORDS = {
    "การ",
    "ความ",
    "เรื่อง",
    "และ",
    "ของ",
    "ที่",
    "ให้",
    "หรือ",
    "กับ",
    "ใหม่",
    "ต่าง",
    "โดย",
    "สำหรับ",
    "จาก",
}

TOPIC_SEMANTIC_KEYWORDS = {
    "วัตถุดิบ",
    "อาหาร",
    "สูตร",
    "ทำเล",
    "ร้าน",
    "ถ่าย",
    "โฆษณา",
    "คลิป",
    "สื่อ",
    "ตัดต่อ",
    "ข้อมูล",
    "login",
    "payment",
    "dashboard",
    "oauth",
    "api",
    "user",
    "mobile",
    "menu",
    "ingredient",
    "location",
    "food",
    "recipe",
    "advertising",
    "shoot",
    "video",
    "buy",
    "cook",
}


def normalize_owner(value: Any) -> str:
    text = str(value or "").strip()
    return text if text else "?"


def group_action_items_by_owner(action_items: Iterable[Dict[str, Any]] | None) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in action_items or []:
        owner = normalize_owner(item.get("owner"))
        grouped.setdefault(owner, []).append(item)
    return grouped


def _topic_match_keywords(topic_text: str) -> set[str]:
    cleaned = re.sub(r"[\-/()\[\]{}.,;:]+", " ", topic_text)
    topic_lower = topic_text.lower()
    keywords = {topic_lower}

    for keyword in TOPIC_SEMANTIC_KEYWORDS:
        if keyword in topic_lower:
            keywords.add(keyword.lower())

    for part in cleaned.split():
        normalized = part.strip().lower()
        if len(normalized) > 2 and normalized not in STOPWORDS:
            keywords.add(normalized)
    return keywords


def summarize_topics_by_owner(topics: Iterable[str] | None, action_items: Iterable[Dict[str, Any]] | None) -> List[Tuple[str, str]]:
    summary: List[Tuple[str, str]] = []
    for topic in topics or []:
        topic_text = str(topic).strip()
        if not topic_text:
            continue

        owner_hint = "?"
        topic_keywords = _topic_match_keywords(topic_text)

        for item in action_items or []:
            task_text = str(item.get("task", "")).lower()
            owner = normalize_owner(item.get("owner"))
            if any(keyword in task_text for keyword in topic_keywords):
                owner_hint = owner
                break

        summary.append((topic_text, owner_hint))

    return summary
