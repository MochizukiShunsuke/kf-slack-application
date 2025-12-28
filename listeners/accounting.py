def handle_accounting_from_command(ack, body, client):
    ack()

    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "accounting_menu_selection",
            "title": {"type": "plain_text", "text": "会計管理メニュー"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "menu_block",
                    "label": {"type": "plain_text", "text": "実行する機能を選択してください"},
                    "element": {
                        "type": "static_select",
                        "action_id": "menu_action",
                        "placeholder": {"type": "plain_text", "text": "機能を選択"},
                        "options": [
                            {"text": {"type": "plain_text", "text": "📷 レシート画像認識"}, "value": "image_recognition"},
                            {"text": {"type": "plain_text", "text": "📝 支出を手動入力"}, "value": "manual_expense"},
                            {"text": {"type": "plain_text", "text": "💰 部費支払い確認"}, "value": "membership_fee"},
                            {"text": {"type": "plain_text", "text": "💸 その他収入入力"}, "value": "other_income"}
                        ]
                    }
                }
            ],
            "submit": {"type": "plain_text", "text": "次へ"}
        }
    )