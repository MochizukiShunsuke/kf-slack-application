SECTION_OPTIONS = [
    { "text": { "type": "plain_text", "text": "フレーム" }, "value": "frame" },
    { "text": { "type": "plain_text", "text": "サスペンション" }, "value": "suspension" },
    { "text": { "type": "plain_text", "text": "ステアリング" }, "value": "steering" },
    { "text": { "type": "plain_text", "text": "外装" }, "value": "aero" },
    { "text": { "type": "plain_text", "text": "コックピット" }, "value": "cockpit" },
    { "text": { "type": "plain_text", "text": "エンジン" }, "value": "engine" },
    { "text": { "type": "plain_text", "text": "燃料・冷却" }, "value": "fuel_cooling" },
    { "text": { "type": "plain_text", "text": "吸気・排気" }, "value": "intake_exhaust" },
    { "text": { "type": "plain_text", "text": "駆動" }, "value": "drivetrain" },
    { "text": { "type": "plain_text", "text": "電装" }, "value": "electrical" }
]

def get_timecard_view():
    return {
        "type": "modal",
        "callback_id": "timecard_submission",
        "title": {"type": "plain_text", "text": "タイムカード"},
        "submit": {"type": "plain_text", "text": "送信"},
        "close": {"type": "plain_text", "text": "戻る"},
        "blocks": [
            {
                "type": "input",
                "block_id": "action_block",
                "label": {"type": "plain_text", "text": "出勤/退勤"},
                "element": {
                    "type": "static_select",
                    "action_id": "action_select",
                    "options": [
                        {"text": {"type": "plain_text", "text": "Check-in (出勤)"}, "value": "CHECK_IN"},
                        {"text": {"type": "plain_text", "text": "Check-out (退勤)"}, "value": "CHECK_OUT"}
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "dept_block",
                "label": {"type": "plain_text", "text": "担当セクション"},
                "element": {
                    "type": "static_select",
                    "action_id": "dept_select",
                    "options": SECTION_OPTIONS
                }
            },
            {
                "type": "input",
                "block_id": "work_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "作業内容"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "work_input",
                    "multiline": True,
                    "placeholder": {"type": "plain_text", "text": "例: フロントサスの組み立て"}
                }
            }
        ]
    }