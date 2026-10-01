from __future__ import annotations

from datetime import date, datetime
import os
import uuid

import streamlit as st
import streamlit.components.v1 as components

from services.meeting_analyzer import analyze_meeting
from services.meeting_formatter import group_action_items_by_owner, summarize_topics_by_owner


st.set_page_config(page_title="AI Meeting Assistant", layout="wide")


UI_TEXT = {
    "th": {
        "meeting_history": "ประวัติการประชุม",
        "new_meeting": "สร้างการประชุมใหม่",
        "meeting_name": "ชื่อการประชุม",
        "meeting_date": "วันที่ประชุม",
        "meeting_transcript": "บันทึกการประชุม",
        "participants": "ผู้เข้าร่วม",
        "add_participant": "เพิ่มผู้เข้าร่วม",
        "remove": "ลบ",
        "analyze_meeting": "วิเคราะห์การประชุม",
        "meeting_information": "ข้อมูลการประชุม",
        "topics_decisions": "หัวข้อและคำตัดสิน",
        "topics": "หัวข้อ",
        "decisions": "คำตัดสิน",
        "action_items": "งานที่ต้องทำ (แยกตามผู้รับผิดชอบ)",
        "action_agreements": "ข้อตกลงและงานที่ต้องทำ",
        "open_issues": "ประเด็นที่เปิดและข้อมูลที่ขาด",
        "summary_by_topic": "สรุปตามหัวข้อ",
        "title": "AI Meeting Assistant",
        "caption": "เปลี่ยนบันทึกการประชุมให้กลายเป็นสรุปแบบมีโครงสร้างและงานที่ต้องทำ",
        "meeting_title": "ชื่อการประชุม",
        "date": "วันที่",
        "participants_label": "ผู้เข้าร่วม",
        "no_participants": "ไม่มีผู้เข้าร่วม",
        "no_topics": "ไม่มีหัวข้อที่ตรวจพบ",
        "no_decisions": "ไม่มีคำตัดสินที่บันทึก",
        "no_action_items": "ไม่มีงานที่ต้องทำ",
        "no_issues": "ไม่มีประเด็นที่เปิด",
        "no_missing": "ไม่มีข้อมูลที่ขาด",
        "no_topic_summary": "ไม่มีสรุปตามหัวข้อ",
        "ai_summary": "สรุป AI",
        "no_history": "ยังไม่มีประวัติการประชุม",
        "language": "ภาษา",
        "theme": "ธีม",
        "light": "สว่าง",
        "dark": "มืด",
        "meeting_placeholder": "การประชุมประจำสัปดาห์ของทีมพัฒนาเว็บไซต์",
        "transcript_placeholder": "วางบันทึกการประชุมที่นี่...",
        "participant_name": "ชื่อผู้เข้าร่วม",
        "participant_role": "บทบาท",
        "meeting_name_required": "ต้องมีชื่อการประชุม",
        "meeting_transcript_required": "ต้องมีบันทึกการประชุม",
        "participant_required": "ต้องมีชื่อผู้เข้าร่วมอย่างน้อย 1 คน",
        "voice_capture": "บันทึกเสียง",
        "voice_capture_status_idle": "พร้อมใช้งาน",
        "voice_capture_status_listening": "กำลังฟัง...",
        "voice_capture_status_unsupported": "เบราว์เซอร์ไม่รองรับ",
    },
    "en": {
        "meeting_history": "Meeting History",
        "new_meeting": "New Meeting",
        "meeting_name": "Meeting Name",
        "meeting_date": "Meeting Date",
        "meeting_transcript": "Meeting Transcript",
        "participants": "Participants",
        "add_participant": "Add Participant",
        "remove": "Remove",
        "analyze_meeting": "Analyze Meeting",
        "meeting_information": "Meeting Information",
        "topics_decisions": "Topics & Decisions",
        "topics": "Topics",
        "decisions": "Decisions",
        "action_items": "Action Items (by owner)",
        "action_agreements": "Agreed Actions",
        "open_issues": "Open Issues & Missing Information",
        "summary_by_topic": "Summary by Topic",
        "title": "AI Meeting Assistant",
        "caption": "Turn meeting notes into structured summaries and follow-up actions.",
        "meeting_title": "Meeting Title",
        "date": "Date",
        "participants_label": "Participants",
        "no_participants": "No participants provided",
        "no_topics": "No topics detected",
        "no_decisions": "No decisions captured",
        "no_action_items": "No action items were generated.",
        "no_issues": "No open issues found",
        "no_missing": "No missing information identified",
        "no_topic_summary": "No topic summary available",
        "ai_summary": "AI Summary",
        "no_history": "No saved meetings yet.",
        "language": "Language",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "meeting_placeholder": "Website Project Weekly Meeting",
        "transcript_placeholder": "Paste meeting transcript here...",
        "participant_name": "Name",
        "participant_role": "Role",
        "meeting_name_required": "Meeting Name is required.",
        "meeting_transcript_required": "Meeting Transcript is required.",
        "participant_required": "Participant Name is required.",
        "voice_capture": "Voice",
        "voice_capture_status_idle": "Ready",
        "voice_capture_status_listening": "Listening...",
        "voice_capture_status_unsupported": "Not supported",
    },
}


def initialize_state() -> None:
    if "meeting_name" not in st.session_state:
        st.session_state.meeting_name = ""
    if "meeting_date" not in st.session_state:
        st.session_state.meeting_date = date.today()
    if "transcript" not in st.session_state:
        st.session_state.transcript = ""
    if "participants" not in st.session_state:
        st.session_state.participants = [{"name": "", "role": ""}]
    if "analysis" not in st.session_state:
        st.session_state.analysis = None
    if "meeting_history" not in st.session_state:
        st.session_state.meeting_history = []
    if "selected_history_id" not in st.session_state:
        st.session_state.selected_history_id = None
    if "ui_language" not in st.session_state:
        st.session_state.ui_language = "th"
    if "theme_mode" not in st.session_state:
        st.session_state.theme_mode = "light"


def t(key: str) -> str:
    language = st.session_state.get("ui_language", "th")
    return UI_TEXT.get(language, UI_TEXT["th"]).get(key, key)


def render_theme_css() -> None:
    theme = st.session_state.get("theme_mode", "light")
    if theme == "dark":
        primary_bg = "#0E1117"
        secondary_bg = "#111827"
        text_color = "#F8FAFC"
        muted = "#B7C2D0"
        card_bg = "#1F2937"
        border = "#374151"
        button_bg = "#111827"
        button_text = "#F8FAFC"
    else:
        primary_bg = "#F7F3EE"
        secondary_bg = "#F1EFEA"
        text_color = "#111111"
        muted = "#4B5563"
        card_bg = "#FFFDFC"
        border = "#D5D0C8"
        button_bg = "#111111"
        button_text = "#F5F5F5"

    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: {primary_bg};
            color: {text_color};
        }}
        section[data-testid="stSidebar"] > div {{
            background-color: {secondary_bg};
            padding-top: 0.5rem;
        }}
        .block-container {{
            padding-top: 1.5rem;
        }}
        div[data-testid="stVerticalBlock"] > div {{
            background-color: transparent;
        }}
        .stButton > button {{
            border-radius: 0.6rem;
            border: 1px solid {border};
            background-color: {button_bg};
            color: {button_text};
            box-shadow: none;
            font-weight: 600;
        }}
        .stTextInput > div > div > input,
        .stTextArea > div > div > textarea,
        .stDateInput > div > div > input {{
            background-color: {card_bg};
            color: {text_color};
            border: 1px solid {border};
        }}
        .stMarkdown {{ color: {text_color}; }}
        .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
        .stTextInput label, .stTextArea label, .stDateInput label, .stSelectbox label,
        .stMultiselect label, .stCheckbox label, .stRadio label {{
            color: {text_color} !important;
        }}
        div[role="alert"] {{
            background-color: {card_bg};
            border: 1px solid {border};
            color: {text_color};
        }}
        div[role="alert"] p, div[role="alert"] div, div[role="alert"] span {{
            color: {text_color} !important;
        }}
        .stCaption {{ color: {muted}; }}
        .theme-toggle-btn {{
            background: {button_bg};
            color: {button_text};
            border: 1px solid {border};
            border-radius: 999px;
            padding: 0.35rem 0.8rem;
            min-width: 48px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def translate_display_text(value: str) -> str:
    if st.session_state.get("ui_language", "th") != "th":
        return value
    replacements = {
        "No blocking issues were identified in the transcript.": "ไม่มีประเด็นที่ขัดขวางตามบันทึกการประชุม",
        "No additional clarification was required based on the transcript.": "ไม่มีข้อมูลเพิ่มเติมที่ต้องขอจากบันทึกการประชุม",
        "No open issues found": "ไม่มีประเด็นที่เปิด",
        "No missing information identified": "ไม่มีข้อมูลที่ขาด",
        "Meeting Information": "ข้อมูลการประชุม",
        "Participants:": "ผู้เข้าร่วม:",
        "Topics & Decisions": "หัวข้อและคำตัดสิน",
        "Topics:": "หัวข้อ:",
        "Decisions:": "คำตัดสิน:",
        "Action Items (แยกตามผู้รับผิดชอบ)": "งานที่ต้องทำ (แยกตามผู้รับผิดชอบ)",
        "Open Issues & Missing Information": "ประเด็นที่เปิดและข้อมูลที่ขาด",
        "Summary by Topic": "สรุปตามหัวข้อ",
        "Meeting Title:": "ชื่อการประชุม:",
        "Date:": "วันที่:",
    }
    return replacements.get(str(value), str(value))


def normalize_history_spacing() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stSidebarNav"] {padding-top: 0.25rem;}
        .block-container {padding-top: 0.75rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def reset_meeting() -> None:
    st.session_state.meeting_name = ""
    st.session_state.meeting_date = date.today()
    st.session_state.transcript = ""
    st.session_state.participants = [{"name": "", "role": ""}]
    st.session_state.analysis = None
    st.session_state.selected_history_id = None


def clean_participants(participants: list[dict]) -> list[dict]:
    cleaned = []
    for participant in participants:
        if not isinstance(participant, dict):
            continue
        name = str(participant.get("name", "")).strip()
        if not name:
            continue
        cleaned.append({
            "name": name,
            "role": str(participant.get("role", "")).strip() or "Not specified",
        })
    return cleaned


def load_meeting_from_history(entry: dict) -> None:
    st.session_state.meeting_name = str(entry.get("name", "")).strip() or "Untitled Meeting"
    meeting_date = entry.get("date")
    if isinstance(meeting_date, str):
        try:
            st.session_state.meeting_date = datetime.strptime(meeting_date, "%Y-%m-%d").date()
        except ValueError:
            st.session_state.meeting_date = date.today()
    else:
        st.session_state.meeting_date = meeting_date or date.today()
    st.session_state.transcript = str(entry.get("transcript", ""))
    participants = entry.get("participants") or [{"name": "", "role": ""}]
    st.session_state.participants = clean_participants(participants) or [{"name": "", "role": ""}]
    st.session_state.analysis = entry.get("analysis")
    st.session_state.selected_history_id = entry.get("id")


def save_current_meeting_to_history() -> None:
    history = list(st.session_state.get("meeting_history", []))
    meeting_name = str(st.session_state.get("meeting_name", "")).strip() or "Untitled Meeting"
    transcript = str(st.session_state.get("transcript", "")).strip()
    participants = clean_participants(st.session_state.get("participants", []))
    analysis = st.session_state.get("analysis")

    if not analysis:
        return

    record = {
        "id": str(uuid.uuid4()),
        "name": meeting_name,
        "date": str(st.session_state.get("meeting_date", date.today())),
        "transcript": transcript,
        "participants": participants,
        "analysis": analysis,
    }

    matching_index = None
    for index, item in enumerate(history):
        if item.get("name") == meeting_name and item.get("transcript") == transcript:
            matching_index = index
            break

    if matching_index is not None:
        history[matching_index] = record
    else:
        history.insert(0, record)

    st.session_state.meeting_history = history[:20]
    st.session_state.selected_history_id = record["id"]


def delete_meeting_from_history(history_id: str) -> None:
    history = [item for item in st.session_state.get("meeting_history", []) if item.get("id") != history_id]
    st.session_state.meeting_history = history
    if st.session_state.get("selected_history_id") == history_id:
        st.session_state.selected_history_id = None
        st.session_state.analysis = None


def render_meeting_history_sidebar() -> None:
    with st.sidebar:
        st.markdown('<div class="theme-corner">', unsafe_allow_html=True)
        lang_label = "TH" if st.session_state.get("ui_language") == "th" else "EN"
        if st.button(lang_label, key="lang_toggle_corner", use_container_width=False):
            st.session_state.ui_language = "en" if st.session_state.get("ui_language") == "th" else "th"
            st.rerun()
        theme_label = "☀️" if st.session_state.get("theme_mode") == "light" else "🌙"
        if st.button(theme_label, key="theme_toggle_corner", use_container_width=False):
            st.session_state.theme_mode = "dark" if st.session_state.get("theme_mode") == "light" else "light"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown(f"<div style='margin-top: 0.25rem; margin-bottom: 0.5rem;'><strong>{t('meeting_history')}</strong></div>", unsafe_allow_html=True)
        history = st.session_state.get("meeting_history", [])
        if st.button(t("new_meeting"), use_container_width=True):
            reset_meeting()
            st.rerun()

        if not history:
            st.caption(t("no_history"))
            return

        for entry in history:
            meeting_name = str(entry.get("name", "Untitled Meeting")).strip() or "Untitled Meeting"
            meeting_date = str(entry.get("date", "")).strip()
            cols = st.columns([4, 1])
            with cols[0]:
                if st.button(meeting_name, key=f"history_item_{entry.get('id')}", use_container_width=True):
                    load_meeting_from_history(entry)
                    st.rerun()
            with cols[1]:
                if st.button("🗑", key=f"delete_history_{entry.get('id')}", use_container_width=True):
                    delete_meeting_from_history(entry.get("id"))
                    st.rerun()
            if meeting_date:
                st.caption(meeting_date)


def render_participants_editor() -> list[dict]:
    participants = st.session_state.get("participants", [{"name": "", "role": ""}])

    st.subheader(t("participants"))
    if st.button(t("add_participant"), key="add_participant_button"):
        participants.append({"name": "", "role": ""})
        st.session_state.participants = participants

    for index, participant in enumerate(participants):
        cols = st.columns([2, 2, 1])
        with cols[0]:
            participant["name"] = st.text_input(
                f"{t('participant_name')} {index + 1}",
                value=participant.get("name", ""),
                key=f"participant_name_{index}",
            )
        with cols[1]:
            participant["role"] = st.text_input(
                f"{t('participant_role')} {index + 1}",
                value=participant.get("role", ""),
                key=f"participant_role_{index}",
            )
        with cols[2]:
            if len(participants) > 1 and st.button(t("remove"), key=f"remove_participant_{index}"):
                participants.pop(index)
                st.session_state.participants = participants
                st.rerun()

    st.session_state.participants = participants
    return participants


def render_create_meeting_page() -> None:
    st.title(t("title"))
    st.caption(t("caption"))

    with st.container():
        meeting_name = st.text_input(
            t("meeting_name"),
            value=st.session_state.meeting_name,
            key="meeting_name_input",
            placeholder=t("meeting_placeholder"),
        )
        st.session_state.meeting_name = meeting_name

        meeting_date = st.date_input(t("meeting_date"), value=st.session_state.meeting_date, key="meeting_date_input")
        st.session_state.meeting_date = meeting_date

        transcript = st.text_area(
            t("meeting_transcript"),
            value=st.session_state.transcript,
            key="transcript_input",
            height=260,
            placeholder=t("transcript_placeholder"),
        )
        st.session_state.transcript = transcript

        render_participants_editor()

        analyze_clicked = st.button(t("analyze_meeting"), use_container_width=True)

        if analyze_clicked:
            errors = []
            if not meeting_name.strip():
                errors.append(t("meeting_name_required"))
            if not transcript.strip():
                errors.append(t("meeting_transcript_required"))

            participants_list = clean_participants(st.session_state.participants)
            if not participants_list or not any(p["name"].strip() for p in participants_list):
                errors.append(t("participant_required"))

            if errors:
                for error in errors:
                    st.warning(error)
                return

            try:
                analysis = analyze_meeting(transcript, participants_list)
                st.session_state.analysis = analysis
                save_current_meeting_to_history()
                source = analysis.get("source")
                has_cohere = bool(os.getenv("COHERE_API_KEY"))
                has_openrouter = bool(os.getenv("OPENROUTER_API_KEY"))

                if source == "openrouter_free_ai":
                    source_label = "OpenRouter AI"
                elif source == "fallback":
                    source_label = "Fallback Summary"
                elif source == "cohere":
                    source_label = "Cohere AI"
                else:
                    source_label = "Mock Analysis"

                if source == "cohere":
                    st.success(f"Meeting analyzed successfully using {source_label}.")
                elif source == "fallback":
                    if not has_cohere and not has_openrouter:
                        st.warning("No API key was detected in the current runtime. The app is using the local fallback summary. Restart Streamlit after setting COHERE_API_KEY or OPENROUTER_API_KEY to use AI analysis.")
                    else:
                        st.warning(f"The app did not complete the AI request successfully. It fell back to the local summary ({source_label}).")
                else:
                    st.info(f"Meeting analyzed successfully using {source_label}.")
            except Exception as exc:  # pragma: no cover - user-facing error handling
                st.error(f"Unable to analyze the meeting. Please try again. Details: {exc}")
                st.session_state.analysis = None


def render_analysis_results() -> None:
    analysis = st.session_state.get("analysis")
    if not analysis:
        return

    meeting_name = st.session_state.get("meeting_name", "")
    meeting_date = st.session_state.get("meeting_date", date.today())
    participants = analysis.get("participants") or clean_participants(st.session_state.get("participants", []))
    participant_names = [participant["name"] for participant in participants if isinstance(participant, dict) and participant.get("name")]
    action_items = analysis.get("action_items", [])
    topics = analysis.get("topics", [])
    decisions = analysis.get("decisions", [])
    grouped = group_action_items_by_owner(action_items)

    st.markdown("---")
    st.subheader(t("meeting_information"))
    st.write(f"{t('meeting_title')}: {meeting_name}")
    st.write(f"{t('date')}: {meeting_date}")
    st.write(f"{t('participants_label')}: {', '.join(participant_names) if participant_names else t('no_participants')}")

    st.subheader(t("topics_decisions"))
    st.write(f"{t('topics')}: {', '.join(str(topic).strip() for topic in topics if str(topic).strip()) or t('no_topics')}")
    st.write(t("decisions") + ":")
    if decisions:
        for decision in decisions:
            st.write(f"- {translate_display_text(str(decision))}")
    else:
        st.write(f"- {t('no_decisions')}")

    st.subheader(t("action_items"))
    if grouped:
        for owner, items in grouped.items():
            st.markdown(f"### {owner}")
            for item in items:
                task = str(item.get("task", "Untitled Action Item")).strip() or "Untitled Action Item"
                st.write(f"[ ] {task}")
    else:
        st.info(t("no_action_items"))

    st.subheader(t("action_agreements"))
    if grouped:
        for owner, items in grouped.items():
            for item in items:
                task = str(item.get("task", "Untitled Action Item")).strip() or "Untitled Action Item"
                st.write(f"[ {owner} ] {task}")
    else:
        st.write(f"- {t('no_action_items')}")

    st.subheader(t("open_issues"))
    issues = analysis.get("open_issues", [])
    if issues:
        for issue in issues:
            st.write(f"- {translate_display_text(str(issue))}")
    else:
        st.write(f"- {t('no_issues')}")

    missing = analysis.get("missing_information", [])
    if missing:
        for item in missing:
            st.write(f"- {translate_display_text(str(item))}")
    else:
        st.write(f"- {t('no_missing')}")

    st.subheader(t("summary_by_topic"))
    topic_summary = summarize_topics_by_owner(topics, action_items)
    if topic_summary:
        for topic, owner in topic_summary:
            st.write(f"- {topic} ({owner})")
    else:
        st.write(f"- {t('no_topic_summary')}")


initialize_state()
render_theme_css()
normalize_history_spacing()

st.markdown(
    """
    <style>
    div[data-testid="stHeader"] {
        position: sticky;
        top: 0;
        z-index: 1000;
        min-height: 2.5rem;
    }
    .theme-corner {
        position: fixed;
        top: 0.55rem;
        right: 0.9rem;
        left: auto;
        z-index: 2000;
        display: flex;
        align-items: center;
        gap: 0.12rem;
        margin: 0;
        padding: 0;
        line-height: 1;
    }
    .theme-corner .stButton {
        margin: 0;
        display: inline-block;
    }
    .theme-corner .stButton > button {
        border: 1px solid rgba(17,17,17,0.15);
        border-radius: 999px;
        background: rgba(255,255,255,0.82);
        color: #111111;
        padding: 0.08rem 0.42rem;
        font-size: 0.62rem;
        font-weight: 700;
        min-width: 0;
        max-width: fit-content;
        height: 1.7rem;
        box-shadow: none;
        line-height: 1;
        margin: 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    render_meeting_history_sidebar()

render_create_meeting_page()
render_analysis_results()
