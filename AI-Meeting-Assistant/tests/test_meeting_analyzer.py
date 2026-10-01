from services.meeting_analyzer import analyze_meeting_mock, normalize_ai_action_items


def test_normalize_ai_action_items_keeps_each_owner_separate():
    items = [
        {"task": "ติดต่อซัพพลายเออร์", "owner": "A", "deadline": "ไม่ระบุ", "priority": "สูง", "status": "ค้าง"},
        {"task": "ทดสอบระบบ login", "owner": "B", "deadline": "ไม่ระบุ", "priority": "สูง", "status": "ค้าง"},
        {"task": "Review meeting action plan", "owner": "A", "deadline": "Not specified", "priority": "Medium", "status": "Pending"},
    ]

    result = normalize_ai_action_items(items, [{"name": "A", "role": "Owner"}, {"name": "B", "role": "Owner"}])

    assert [item["owner"] for item in result] == ["A", "B"]
    assert any("ซัพพลายเออร์" in item["task"] for item in result)
    assert any("login" in item["task"].lower() for item in result)
    assert all("Review meeting action plan" not in item["task"] for item in result)


def test_analyze_meeting_mock_extracts_multiple_owners_from_simple_meeting_transcript():
    transcript = '''
    สวัสดีครับ B วันนี้เรามาสรุปงานกันหน่อยนะ โอเค...
    งานแรกเลย เดี๋ยว A จะออกไปซื้อของวัตถุดิบข้างนอกให้ แล้ว B ช่วยเอาวัตถุดิบพวกนี้มาลองทำกับข้าวนะ
    พอ B ทำเสร็จเรียบร้อยแล้ว เดี๋ยว A จะเป็นคนเอาเมนูนั้นไปถ่ายโฆษณาแล้วเอาคลิปมาตัดต่อเองครับ
    ได้เลย A งั้นเดี๋ยวระหว่างที่ B รอ A ออกไปซื้อของ B จะไปนั่งคิดสูตรอาหารใหม่ๆ ไว้รอเลยนะ
    ดีเลยครับ B แล้วก็งานสุดท้าย เดี๋ยว A จะออกไปติดต่อหาทำเลร้านใหม่ให้ด้วยครับ
    '''

    result = analyze_meeting_mock(transcript, [{"name": "A", "role": "Owner"}, {"name": "B", "role": "Owner"}])

    owners = {item["owner"] for item in result["action_items"]}
    assert {"A", "B"}.issubset(owners)
    assert any("ซื้อ" in item["task"] or "วัตถุดิบ" in item["task"] for item in result["action_items"])
    assert any("สูตรอาหาร" in item["task"] or "ทำอาหาร" in item["task"] for item in result["action_items"])
