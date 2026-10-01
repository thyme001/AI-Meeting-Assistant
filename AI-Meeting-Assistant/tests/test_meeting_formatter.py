from services.meeting_formatter import group_action_items_by_owner, summarize_topics_by_owner


def test_group_action_items_by_owner_uses_question_for_unknown_owner():
    grouped = group_action_items_by_owner([
        {"task": "Buy ingredients", "owner": "A"},
        {"task": "Prepare food", "owner": ""},
        {"task": "Shoot ad video", "owner": "B"},
    ])

    assert grouped["A"][0]["task"] == "Buy ingredients"
    assert grouped["?"][0]["task"] == "Prepare food"
    assert grouped["B"][0]["task"] == "Shoot ad video"


def test_summarize_topics_by_owner_prioritizes_known_owner():
    topics = [
        "การเตรียมวัตถุดิบและทำอาหาร",
        "การถ่ายทำสื่อโฆษณา",
        "การหาทำเลร้าน",
    ]
    action_items = [
        {"task": "ออกไปซื้อของ/วัตถุดิบ", "owner": "A"},
        {"task": "นำอาหารที่ B ทำไปถ่ายโฆษณาและตัดต่อคลิป", "owner": "A"},
        {"task": "ออกไปติดต่อหาทำเลร้านใหม่", "owner": "A"},
    ]

    summary = summarize_topics_by_owner(topics, action_items)

    assert summary[0][0] == "การเตรียมวัตถุดิบและทำอาหาร"
    assert summary[0][1] == "A"
    assert summary[1][1] == "A"
    assert summary[2][1] == "A"
