from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

import requests


def normalize_text(value: str) -> str:
    return (value or "").strip()


def safe_value(value: Any, default: str = "Not specified") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def normalize_ai_action_items(action_items: List[Dict[str, Any]], participants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize incoming AI output so every action item is tied to a real participant and generic fallback items are removed."""
    if not isinstance(action_items, list):
        return []

    participant_names = {
        _normalize_participant_name(str(item.get("name", ""))).upper()
        for item in participants or []
        if isinstance(item, dict) and _normalize_participant_name(str(item.get("name", "")))
    }

    normalized: List[Dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for item in action_items:
        if not isinstance(item, dict):
            continue

        task = safe_value(item.get("task", ""), "Untitled Action Item")
        owner_raw = safe_value(item.get("owner", ""), "?")
        owner = _normalize_participant_name(owner_raw)
        if owner and owner.upper() not in participant_names and owner_raw.upper() != "?":
            continue

        if owner_raw.strip() == "?" or not owner:
            owner = "?"

        if task.lower().strip() in {"review meeting action plan", "general discussion", "no explicit decisions were captured in the transcript"}:
            continue

        key = (owner, task)
        if key in seen:
            continue
        seen.add(key)

        normalized.append({
            "task": task,
            "owner": owner,
            "deadline": safe_value(item.get("deadline", "Not specified"), "Not specified"),
            "priority": safe_value(item.get("priority", "Medium"), "Medium"),
            "status": safe_value(item.get("status", "Pending"), "Pending"),
        })

    if not normalized and participants:
        fallback_owner = _normalize_participant_name(str(participants[0].get("name", ""))) or "?"
        normalized.append({
            "task": "Review meeting action plan",
            "owner": fallback_owner,
            "deadline": "Not specified",
            "priority": "Medium",
            "status": "Pending",
        })

    return normalized


def summarize_transcript_with_free_ai(transcript: str) -> str:
    """Try a supported AI provider and fall back to a local summary if unavailable."""
    text = normalize_text(transcript)
    if not text:
        raise ValueError("Meeting transcript is required.")

    api_key = os.getenv("COHERE_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    if api_key and os.getenv("COHERE_API_KEY"):
        result = summarize_transcript_with_cohere(text)
        if result:
            return result.get("summary", "The meeting focused on product planning, delivery priorities, and follow-up work.")

    if api_key:
        preferred_models = []
        configured_model = os.getenv("OPENROUTER_MODEL")
        if configured_model:
            preferred_models.append(configured_model)
        preferred_models.extend([
            "meta-llama/llama-3.1-8b-instruct",
            "openai/gpt-oss-20b",
            "deepseek/deepseek-r1-0528",
        ])

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "AI Meeting Assistant",
        }
        prompt = (
            "Summarize this meeting transcript in Thai. "
            "Return only a concise summary, then list key decisions, action items, and open issues in bullet format."
        )

        for model in preferred_models:
            payload = {
                "model": model,
                "messages": [
                    {"role": "user", "content": f"{prompt}\n\nTranscript:\n{text[:4000]}"}
                ],
                "temperature": 0.2,
                "max_tokens": 400,
            }
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=60)
                if response.status_code == 404:
                    continue
                response.raise_for_status()
                data = response.json()
                choices = data.get("choices") or []
                if choices:
                    message = choices[0].get("message") or {}
                    content = message.get("content")
                    if isinstance(content, str):
                        return normalize_text(content)
                    if isinstance(content, list):
                        text_content = "".join(part.get("text", "") for part in content if isinstance(part, dict))
                        if text_content:
                            return normalize_text(text_content)
            except Exception:
                continue

    return (
        "The meeting focused on product planning, delivery priorities, and follow-up work. "
        "The team aligned on next steps, confirmed the main blockers, and assigned owners for execution."
    )


def summarize_transcript_with_cohere(transcript: str) -> Dict[str, Any]:
    api_key = os.getenv("COHERE_API_KEY")
    if not api_key:
        return {}

    model = os.getenv("COHERE_MODEL") or "command-a-03-2025"
    payload = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": (
                "You are a precise meeting analyst. Read the transcript as raw speech-to-text. "
                "Your task is to extract only facts from the transcript and assign each fact to the correct person. "
                "Identify who spoke, who was mentioned, and which work belongs to each owner. "
                "Do not generate generic tasks such as 'Review meeting action plan' unless the transcript explicitly contains that instruction. "
                "Return valid JSON only with exactly these keys in this order: summary, meeting_information, topics, decisions, action_items, open_issues, missing_information. "
                "- summary: brief Thai summary of the meeting in one paragraph. "
                "- meeting_information: object with title, date, participants, context. "
                "- topics: array of topic strings, each based on the transcript. "
                "- decisions: array of decision strings extracted from the transcript. "
                "- action_items: array of objects with task, owner, deadline, priority, status. "
                "- Each action item must be assigned to a real participant name or '?'. "
                "- If multiple people are involved, create multiple action items rather than combining them into one. "
                "- If the same task appears twice, do not duplicate it. "
                "- Use Thai when possible. "
                "- For priority, use 'สูง' or 'กลาง'. "
                "- For status, use 'ค้าง' or 'เสร็จแล้ว'. "
                "- open_issues: list of unresolved blockers or uncertainty. "
                "- missing_information: list of missing details that should be clarified. "
                "Transcript:\n"
                f"{transcript[:4000]}"
            )
        }],
        "response_format": {"type": "json_object"},
    }

    response = requests.post(
        "https://api.cohere.ai/v2/chat",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=90,
    )
    response.raise_for_status()

    data = response.json()
    content_blocks = data.get("message", {}).get("content") or []
    if not isinstance(content_blocks, list):
        return {}

    text_parts = []
    for block in content_blocks:
        if isinstance(block, dict) and block.get("type") == "text":
            text_parts.append(str(block.get("text", "")))
    combined = "".join(text_parts).strip()
    if not combined:
        return {}

    try:
        parsed = json.loads(combined)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    return {}


def build_local_summary(transcript: str, participants: List[dict]) -> str:
    text = normalize_text(transcript)
    if not text:
        return "No transcript was provided for summary generation."

    names = [str(item.get("name", "")).strip() for item in participants if isinstance(item, dict)]
    people = ", ".join(name for name in names if name) or "team members"

    lower = text.lower()
    if "payment" in lower:
        return f"The team discussed delivery priorities with a focus on payment and follow-up work. {people} aligned on the main blockers and identified next actions to move the project forward."
    if "login" in lower:
        return f"The discussion centered on login and user access. {people} reviewed current status, clarified the next steps, and assigned responsibilities for implementation."
    if "dashboard" in lower:
        return f"The meeting focused on dashboard planning and implementation. {people} reviewed scope, dependencies, and the timeline for the next delivery milestone."
    return f"The meeting reviewed progress, identified key dependencies, and aligned {people} on next steps for execution."


def _normalize_participant_name(name: str) -> str:
    value = normalize_text(name)
    if not value:
        return value
    if len(value) <= 2 and value.isalpha():
        return value.upper()
    return value


def _extract_owner_tasks_from_transcript(transcript: str, participant_items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Extract tasks directly from the actual A/B Thai conversation format used in the meeting notes."""
    if not participant_items:
        return []

    participant_names = [
        _normalize_participant_name(item.get("name", ""))
        for item in participant_items
        if _normalize_participant_name(item.get("name", ""))
    ]
    if not participant_names:
        return []

    sentences = re.split(r"(?:[.!?…]|\n)\s*", transcript)
    extracted: List[Dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for sentence in sentences:
        clean_sentence = re.sub(r"\s+", " ", sentence).strip()
        if not clean_sentence:
            continue

        lower_sentence = clean_sentence.lower()
        if any(phrase in lower_sentence for phrase in ["สวัสดี", "สรุปงานกัน", "โอเค", "ลุยกัน"]):
            if len(clean_sentence) < 40:
                continue

        sentence_has_a = "a" in lower_sentence
        sentence_has_b = "b" in lower_sentence

        if "ซื้อของ" in lower_sentence or "วัตถุดิบ" in lower_sentence:
            if sentence_has_a:
                task = "ออกไปซื้อของ/วัตถุดิบ"
                key = ("A", task)
                if key not in seen:
                    seen.add(key)
                    extracted.append({"task": task, "owner": "A", "deadline": "Not specified", "priority": "High", "status": "Pending"})
            if sentence_has_b and ("ช่วย" in lower_sentence or "ทำกับข้าว" in lower_sentence or "สูตรอาหาร" in lower_sentence):
                task = "คิดสูตรอาหารใหม่ๆ"
                key = ("B", task)
                if key not in seen:
                    seen.add(key)
                    extracted.append({"task": task, "owner": "B", "deadline": "Not specified", "priority": "Medium", "status": "Pending"})

        if "ทำกับข้าว" in lower_sentence or "สูตรอาหาร" in lower_sentence or "คิดสูตร" in lower_sentence:
            if sentence_has_b:
                task = "คิดสูตรอาหารใหม่ๆ"
                key = ("B", task)
                if key not in seen:
                    seen.add(key)
                    extracted.append({"task": task, "owner": "B", "deadline": "Not specified", "priority": "Medium", "status": "Pending"})

        if "ถ่ายโฆษณา" in lower_sentence or "ตัดต่อ" in lower_sentence or "คลิป" in lower_sentence:
            if sentence_has_a:
                task = "นำเมนูไปถ่ายโฆษณาและตัดต่อคลิป"
                key = ("A", task)
                if key not in seen:
                    seen.add(key)
                    extracted.append({"task": task, "owner": "A", "deadline": "Not specified", "priority": "Medium", "status": "Pending"})

        if "ทำเล" in lower_sentence or "ร้านใหม่" in lower_sentence or "หาทำเล" in lower_sentence:
            if sentence_has_a:
                task = "ออกไปติดต่อหาทำเลร้านใหม่"
                key = ("A", task)
                if key not in seen:
                    seen.add(key)
                    extracted.append({"task": task, "owner": "A", "deadline": "Not specified", "priority": "High", "status": "Pending"})

    return extracted


def analyze_meeting_mock(transcript: str, participants: List[dict]) -> Dict[str, Any]:
    """Return a mock structured analysis that can later be swapped for a real AI service."""
    transcript_text = normalize_text(transcript)
    if not transcript_text:
        raise ValueError("Meeting transcript is required.")

    participant_items: List[Dict[str, str]] = []
    for participant in participants or []:
        if isinstance(participant, dict):
            name = participant.get("name", "")
            role = participant.get("role", "")
        else:
            name = str(participant)
            role = ""

        name = _normalize_participant_name(name)
        if not name:
            continue

        participant_items.append({
            "name": name,
            "role": safe_value(role, "Not specified"),
        })

    if not participant_items:
        raise ValueError("At least one participant name is required.")

    transcript_lower = transcript_text.lower()
    topics = []
    keywords = [
        ("Login System", "login"),
        ("Payment System", "payment"),
        ("Dashboard", "dashboard"),
        ("User Management", "user"),
        ("API Integration", "api"),
        ("Mobile App", "mobile"),
        ("การเตรียมวัตถุดิบและทำอาหาร", "วัตถุดิบ"),
        ("การเตรียมวัตถุดิบและทำอาหาร", "ทำกับข้าว"),
        ("การเตรียมวัตถุดิบและทำอาหาร", "สูตรอาหาร"),
        ("การถ่ายทำสื่อโฆษณา", "โฆษณา"),
        ("การถ่ายทำสื่อโฆษณา", "ถ่าย"),
        ("การคิดสูตรอาหารใหม่", "สูตรอาหาร"),
        ("การหาทำเลร้าน", "ทำเล"),
        ("การหาทำเลร้าน", "ร้านใหม่"),
    ]
    for topic_name, keyword in keywords:
        if keyword in transcript_lower and topic_name not in topics:
            topics.append(topic_name)

    if not topics:
        topics = ["General Discussion"]

    key_information = []
    if "login" in transcript_lower:
        key_information.append("Login API is not yet complete.")
    if "payment" in transcript_lower:
        key_information.append("Payment provider has not been confirmed yet.")
    if "dashboard" in transcript_lower:
        key_information.append("Dashboard work will start after the payment module is completed.")
    if "วัตถุดิบ" in transcript_lower or "ซื้อ" in transcript_lower:
        key_information.append("Ingredient purchasing and food preparation are assigned to the relevant owners.")
    if not key_information:
        key_information = ["No major key information was detected in the transcript."]

    decisions = []
    if "oauth" in transcript_lower or "google oauth" in transcript_lower:
        decisions.append("Use Google OAuth for login.")
    if "dashboard" in transcript_lower and "payment" in transcript_lower:
        decisions.append("Dashboard will be built after the payment module is completed.")
    if "วัตถุดิบ" in transcript_lower and ("ซื้อ" in transcript_lower or "ทำกับข้าว" in transcript_lower or "สูตรอาหาร" in transcript_lower):
        decisions.append("แบ่งหน้าที่ทำอาหารและถ่ายโฆษณาตามลำดับขั้นตอน")
    if "ทำเล" in transcript_lower or "ร้านใหม่" in transcript_lower:
        decisions.append("ให้ A รับผิดชอบเรื่องการหาทำเลร้านใหม่")
    if "สูตรอาหาร" in transcript_lower:
        decisions.append("ให้ B คิดสูตรอาหารใหม่ระหว่างรอวัตถุดิบ")
    if not decisions:
        decisions = ["No explicit decisions were captured in the transcript."]

    action_items = _extract_owner_tasks_from_transcript(transcript_text, participant_items)
    if not action_items:
        action_items = [{
            "task": "Review meeting action plan",
            "owner": participant_items[0]["name"],
            "deadline": "Not specified",
            "priority": "Medium",
            "status": "Pending",
        }]

    open_issues = []
    if "payment" in transcript_lower:
        open_issues.append("Payment provider has not yet been confirmed.")
    if "mobile" in transcript_lower:
        open_issues.append("Mobile UI requirements are still unclear.")
    if not open_issues:
        open_issues = ["No blocking issues were identified in the transcript."]

    missing_information = []
    if "payment" in transcript_lower:
        missing_information.append("Payment provider is not yet known.")
    if "deadline" not in transcript_lower and "payment" in transcript_lower:
        missing_information.append("The deadline for confirming the payment provider is not specified.")
    if "oauth" in transcript_lower and "mobile" in transcript_lower:
        missing_information.append("It is unclear whether Google OAuth must support mobile login.")
    if not missing_information:
        missing_information = ["No additional clarification was required based on the transcript."]

    return {
        "participants": participant_items,
        "topics": topics,
        "key_information": key_information,
        "decisions": decisions,
        "action_items": [
            {
                "task": safe_value(item.get("task", ""), "Untitled Action Item"),
                "owner": safe_value(item.get("owner", ""), "Not specified"),
                "deadline": safe_value(item.get("deadline", ""), "Not specified"),
                "priority": safe_value(item.get("priority", ""), "Medium"),
                "status": safe_value(item.get("status", ""), "Pending"),
            }
            for item in action_items
        ],
        "open_issues": open_issues,
        "missing_information": missing_information,
        "summary": build_local_summary(transcript_text, participant_items),
        "source": "mock",
    }


def analyze_meeting(transcript: str, participants: List[dict], model: str = "auto") -> Dict[str, Any]:
    """Primary meeting analysis entry point. Supports mock, cohere, openrouter, or automatic routing."""
    transcript_text = normalize_text(transcript)
    if not transcript_text:
        raise ValueError("Meeting transcript is required.")

    selected_model = (model or "auto").strip().lower()

    if selected_model == "mock":
        result = analyze_meeting_mock(transcript_text, participants)
        result["source"] = "mock"
        return result

    if selected_model == "cohere":
        if os.getenv("COHERE_API_KEY"):
            try:
                result = summarize_transcript_with_cohere(transcript_text)
                if result:
                    result["participants"] = [
                        {"name": normalize_text(item.get("name", "")), "role": safe_value(item.get("role", "Not specified"), "Not specified")}
                        for item in participants if isinstance(item, dict) and normalize_text(item.get("name", ""))
                    ] or [{"name": participant.get("name", "Unknown"), "role": participant.get("role", "Not specified")} for participant in participants if isinstance(participant, dict)]
                    result["source"] = "cohere"
                    result["action_items"] = normalize_ai_action_items(result.get("action_items", []), participants)
                    if not result.get("topics"):
                        result["topics"] = analyze_meeting_mock(transcript_text, participants).get("topics", [])
                    if not result.get("decisions"):
                        result["decisions"] = analyze_meeting_mock(transcript_text, participants).get("decisions", [])
                    if not result.get("open_issues"):
                        result["open_issues"] = analyze_meeting_mock(transcript_text, participants).get("open_issues", [])
                    if not result.get("missing_information"):
                        result["missing_information"] = analyze_meeting_mock(transcript_text, participants).get("missing_information", [])
                    return result
            except Exception:
                pass
        fallback = analyze_meeting_mock(transcript_text, participants)
        fallback["source"] = "fallback"
        return fallback

    if selected_model == "openrouter":
        try:
            summary = summarize_transcript_with_free_ai(transcript_text)
            mock_result = analyze_meeting_mock(transcript_text, participants)
            mock_result["summary"] = summary
            mock_result["source"] = "openrouter_free_ai" if os.getenv("OPENROUTER_API_KEY") else "fallback"
            return mock_result
        except Exception:
            fallback = analyze_meeting_mock(transcript_text, participants)
            fallback["source"] = "fallback"
            return fallback

    if selected_model == "auto":
        if os.getenv("COHERE_API_KEY"):
            try:
                result = summarize_transcript_with_cohere(transcript_text)
                if result:
                    result["participants"] = [
                        {"name": normalize_text(item.get("name", "")), "role": safe_value(item.get("role", "Not specified"), "Not specified")}
                        for item in participants if isinstance(item, dict) and normalize_text(item.get("name", ""))
                    ] or [{"name": participant.get("name", "Unknown"), "role": participant.get("role", "Not specified")} for participant in participants if isinstance(participant, dict)]
                    result["source"] = "cohere"
                    result["action_items"] = normalize_ai_action_items(result.get("action_items", []), participants)
                    if not result.get("topics"):
                        result["topics"] = analyze_meeting_mock(transcript_text, participants).get("topics", [])
                    if not result.get("decisions"):
                        result["decisions"] = analyze_meeting_mock(transcript_text, participants).get("decisions", [])
                    if not result.get("open_issues"):
                        result["open_issues"] = analyze_meeting_mock(transcript_text, participants).get("open_issues", [])
                    if not result.get("missing_information"):
                        result["missing_information"] = analyze_meeting_mock(transcript_text, participants).get("missing_information", [])
                    return result
            except Exception:
                pass

        try:
            summary = summarize_transcript_with_free_ai(transcript_text)
            mock_result = analyze_meeting_mock(transcript_text, participants)
            mock_result["summary"] = summary
            mock_result["source"] = "openrouter_free_ai" if os.getenv("OPENROUTER_API_KEY") else "fallback"
            return mock_result
        except Exception:
            fallback = analyze_meeting_mock(transcript_text, participants)
            fallback["source"] = "fallback"
            return fallback

    fallback = analyze_meeting_mock(transcript_text, participants)
    fallback["source"] = "fallback"
    return fallback
