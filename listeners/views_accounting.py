from datetime import datetime
import threading
import logging

logger = logging.getLogger(__name__)


# ============================================================
# 1. 定数・共通設定
# ============================================================


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




# ============================================================
# 2. エントリーポイント (メニュー遷移)
# ============================================================


def handle_menu_selection(ack, body, client):
    view_state = body["view"]["state"]["values"]
    user_id = body["user"]["id"]
    
    try:
        selected_menu = view_state["menu_block"]["menu_action"]["selected_option"]["value"]
    except KeyError:
        ack()
        return

    if selected_menu == "image_recognition":
        ack(response_action="update", view=get_receipt_input_view())
    elif selected_menu == "manual_expense":
        ack(response_action="update", view=get_manual_expense_view())
    elif selected_menu == "membership_fee":
        ack(response_action="update", view=get_membership_fee_view())
    elif selected_menu == "other_income":
        ack(response_action="update", view=get_other_income_view())
    else:
        ack()
        client.chat_postMessage(channel=user_id, text="⚠️ 未実装のメニューです。")




# ============================================================
# 3. モーダルUIの定義 (View構成)
# ============================================================


def get_receipt_input_view():
    return {
        "type": "modal",
        "callback_id": "accounting_receipt_input",
        "title": {"type": "plain_text", "text": "支出入力(レシート画像認識)"},
        "submit": {"type": "plain_text", "text": "送信"},
        "close": {"type": "plain_text", "text": "戻る"},
        "blocks": [
            {"type": "input", "block_id": "receipt", "label": {"type": "plain_text", "text": "レシート画像"}, "element": {"type": "file_input", "action_id": "file"}},
            {"type": "input", "block_id": "category", "label": {"type": "plain_text", "text": "種類"}, "element": {"type": "static_select", "action_id": "value", "options": [{"text": {"type": "plain_text", "text": "車両製作費"}, "value": "vehicle"}, {"text": {"type": "plain_text", "text": "移動費"}, "value": "travel"}, {"text": {"type": "plain_text", "text": "設備費"}, "value": "equipment"}, {"text": {"type": "plain_text", "text": "活動費"}, "value": "activity"}, {"text": {"type": "plain_text", "text": "その他"}, "value": "other"}]}},
            {"type": "input", "block_id": "section_block", "optional": True, "label": {"type": "plain_text", "text": "セクション"}, "element": {"type": "static_select", "action_id": "value", "options": SECTION_OPTIONS}},
            {"type": "input", "block_id": "payer", "label": {"type": "plain_text", "text": "支払者"}, "element": {"type": "plain_text_input", "action_id": "value"}},
            {"type": "input", "block_id": "settlement", "optional": True, "label": {"type": "plain_text", "text": "精算"}, "element": {"type": "radio_buttons", "action_id": "value", "options": [{"text": {"type": "plain_text", "text": "✅ 精算済み"}, "value": "true"}, {"text": {"type": "plain_text", "text": "❎ 未精算"}, "value": "false"}]}}
        ]
    }


def get_manual_expense_view(item_count=1, current_state=None):
    today = datetime.now().strftime("%Y-%m-%d")
    vals = {}
    reset_id = "0"
    metadata = f"{item_count}_0"

    if current_state:
        metadata = current_state.get("private_metadata", f"{item_count}_0")
        vals = current_state.get("state", {}).get("values", {})
        if not vals:
            vals = current_state.get("values", {})
    
    parts = metadata.split("_")
    reset_id = parts[1] if len(parts) > 1 else "0"
    init_date = vals.get("date_block", {}).get("date_selection", {}).get("selected_date") or today
    blocks = [
        {"type": "input", "block_id": "date_block", "label": {"type": "plain_text", "text": "日付を選択"}, "element": {"type": "datepicker", "action_id": "date_selection", "initial_date": init_date}},
        {"type": "divider"}
    ]
    total = 0
    summary_lines = []

    for i in range(item_count):
        curr_name_id = f"item_name_{i}_{reset_id}"
        curr_amt_id = f"item_amt_{i}_{reset_id}"
        
        raw_name = vals.get(curr_name_id, {}).get("name_action", {}).get("value") or ""
        raw_amt = vals.get(curr_amt_id, {}).get("price_action", {}).get("value")
        
        current_amt = 0
        if raw_amt is not None and str(raw_amt).strip() != "":
            try:
                current_amt = int(float(str(raw_amt)))
                total += current_amt
            except: pass

        if raw_name or current_amt > 0:
            summary_lines.append(f"・{raw_name or '---'}: ¥{current_amt:,}")

        amt_element = {
            "type": "number_input",
            "is_decimal_allowed": False,
            "action_id": "price_action",
            "dispatch_action_config": {"trigger_actions_on": ["on_character_entered"]}
        }
        if raw_amt is not None and str(raw_amt).strip() != "":
            amt_element["initial_value"] = str(raw_amt)

        blocks.extend([
            {
                "type": "input", "block_id": curr_name_id,
                "label": {"type": "plain_text", "text": f"品目 {i+1}"},
                "element": {"type": "plain_text_input", "action_id": "name_action", "initial_value": str(raw_name), "placeholder": {"type": "plain_text", "text": "例: タイヤ"}}
            },
            {
                "type": "input", "block_id": curr_amt_id,
                "label": {"type": "plain_text", "text": f"金額 {i+1}"},
                "element": amt_element
            }
        ])

    summary_text = "\n".join(summary_lines) if summary_lines else "（入力なし）"
    blocks.extend([
        {
            "type": "section",
            "block_id": "total_display",
            "text": {"type": "mrkdwn", "text": f"*現在の合計: ¥{total:,}*\n{summary_text}"},
            "accessory": {"type": "button", "text": {"type": "plain_text", "text": "🔄 再計算"}, "action_id": "refresh_total", "style": "primary"}
        },
        {
            "type": "actions", "block_id": "item_controls",
            "elements": [
                {"type": "button", "text": {"type": "plain_text", "text": "➕ 項目を追加"}, "action_id": "add_item", "value": str(item_count)},
                {"type": "button", "text": {"type": "plain_text", "text": "➖ 削除"}, "action_id": "remove_item", "value": str(item_count), "style": "danger"}
            ]
        }
    ])

    blocks.append({"type": "divider"})

    cat_element = {
        "type": "static_select", 
        "action_id": "value", 
        "options": [
            {"text": {"type": "plain_text", "text": "車両製作費"}, "value": "vehicle"},
            {"text": {"type": "plain_text", "text": "移動費"}, "value": "travel"},
            {"text": {"type": "plain_text", "text": "設備費"}, "value": "equipment"},
            {"text": {"type": "plain_text", "text": "活動費"}, "value": "activity"},
            {"text": {"type": "plain_text", "text": "その他"}, "value": "other"}
        ]
    }
    sel_cat = vals.get("category", {}).get("value", {}).get("selected_option")
    if sel_cat: cat_element["initial_option"] = sel_cat
    blocks.append({"type": "input", "block_id": "category", "label": {"type": "plain_text", "text": "種類"}, "element": cat_element})

    sec_element = {"type": "static_select", "action_id": "value", "options": SECTION_OPTIONS}
    sel_sec = vals.get("section_block", {}).get("value", {}).get("selected_option")
    if sel_sec: sec_element["initial_option"] = sel_sec
    blocks.append({"type": "input", "block_id": "section_block", "optional": True, "label": {"type": "plain_text", "text": "セクション"}, "element": sec_element})

    init_payer = vals.get("payer", {}).get("value", {}).get("value") or ""
    blocks.append({"type": "input", "block_id": "payer", "label": {"type": "plain_text", "text": "支払者"}, "element": {"type": "plain_text_input", "action_id": "value", "initial_value": init_payer}})

    set_element = {
        "type": "radio_buttons", "action_id": "value", 
        "options": [{"text": {"type": "plain_text", "text": "✅ 精算済み"}, "value": "true"}, {"text": {"type": "plain_text", "text": "❎ 未精算"}, "value": "false"}]
    }
    sel_set = vals.get("settlement", {}).get("value", {}).get("selected_option")
    if sel_set: set_element["initial_option"] = sel_set
    blocks.append({"type": "input", "block_id": "settlement", "optional": True, "label": {"type": "plain_text", "text": "精算"}, "element": set_element})

    return {
            "type": "modal",
            "callback_id": "manual_expense_submission",
            "private_metadata": f"{item_count}_{reset_id}", # 状態を保持
            "title": {"type": "plain_text", "text": "支出入力(手動)"},
            "submit": {"type": "plain_text", "text": "送信"},
            "close": {"type": "plain_text", "text": "戻る"},
            "blocks": blocks
        }


def get_membership_fee_view():
    return {
        "type": "modal",
        "callback_id": "membership_fee_submission",
        "title": {"type": "plain_text", "text": "部費支払い確認"},
        "submit": {"type": "plain_text", "text": "確認"},
        "close": {"type": "plain_text", "text": "戻る"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "確認したい部員を選択するか、直接名前を入力してください。"}
            },
            {
                "type": "input",
                "block_id": "user_selection_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "Slackユーザーから選択"},
                "element": {
                    "type": "users_select",
                    "placeholder": {"type": "plain_text", "text": "ユーザーを選択"},
                    "action_id": "user_action"
                }
            },
            {
                "type": "input",
                "block_id": "manual_name_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "手動入力 (Slackにいない場合)"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "name_action",
                    "placeholder": {"type": "plain_text", "text": "例：山田 太郎"}
                }
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "※両方入力された場合は手動入力が優先されます。"}
                ]
            }
        ]
    }


def get_other_income_view(current_state=None):

    today = datetime.now().strftime("%Y-%m-%d")
    vals = {}

    if current_state:
        vals = current_state.get("state", {}).get("values", {})
        if not vals:
            vals = current_state.get("values", {})

    init_date = vals.get("date_block", {}).get("date_selection", {}).get("selected_date") or today

    return {
        "type": "modal",
        "callback_id": "other_income_submission",
        "title": {"type": "plain_text", "text": "その他収入入力"},
        "submit": {"type": "plain_text", "text": "送信"},
        "close": {"type": "plain_text", "text": "戻る"},
        "blocks": [
            {"type": "input", "block_id": "date_block", "label": {"type": "plain_text", "text": "日付を選択"}, "element": {"type": "datepicker", "action_id": "date_selection", "initial_date": init_date}},
            {"type": "input", "block_id": "content", "label": {"type": "plain_text", "text": "内容"}, "element": {"type": "plain_text_input", "action_id": "value"}},
            {
                "type": "input", 
                "block_id": "amount", 
                "label": {"type": "plain_text", "text": "金額 (円)"}, 
                "element": {
                    "type": "number_input", 
                    "is_decimal_allowed": False,
                    "action_id": "value",
                    "placeholder": {"type": "plain_text", "text": "数字のみ入力してください"}
                }
            }
        ]
    }




# ============================================================
# 4. UIイベントハンドラー (動的更新)
# ============================================================


def handle_modal_update(ack, body, client):
    ack()
    try:
        view = body["view"]
        metadata = view.get("private_metadata", "1_0")
        parts = metadata.split("_")
        count = int(parts[0])
        reset_id = int(parts[1]) if len(parts) > 1 else 0
        
        action_id = body["actions"][0]["action_id"]

        if action_id == "add_item":
            vals = view["state"]["values"]
            last = count - 1
            n = vals.get(f"item_name_{last}_{reset_id}", {}).get("name_action", {}).get("value")
            a = vals.get(f"item_amt_{last}_{reset_id}", {}).get("price_action", {}).get("value")
            if not n or not a: return 
            count += 1
        elif action_id == "remove_item":
            if count == 1:
                reset_id += 1
                new_view = get_manual_expense_view(1, {"private_metadata": f"1_{reset_id}"})
                client.views_update(view_id=view["id"], hash=view["hash"], view=new_view)
                return
            else:
                count = max(1, count - 1)

        client.views_update(
            view_id=view["id"],
            hash=view["hash"],
            view=get_manual_expense_view(count, view) 
        )
    except Exception as e:
        logger.error(f"Update error: {e}")




# ============================================================
# 5. 提出処理のハンドラー (Submission)
# ============================================================


def handle_manual_expense_submission(ack, body, client):
    view_state = body["view"]["state"]["values"]
    metadata = body["view"].get("private_metadata", "1_0")
    item_count = int(metadata.split("_")[0])
    user_id = body["user"]["id"]

    details, prices, total, errors = [], [], 0, {}

    # 品目と金額の抽出
    for i in range(item_count):
        name, price = None, None
        for block_id, actions in view_state.items():
            if block_id.startswith(f"item_name_{i}_"):
                name = actions.get("name_action", {}).get("value")
            if block_id.startswith(f"item_amt_{i}_"):
                price = actions.get("price_action", {}).get("value")
        
        if not name: errors[next(k for k in view_state if k.startswith(f"item_name_{i}_"))] = "品目名を入力してください"
        if not price: errors[next(k for k in view_state if k.startswith(f"item_amt_{i}_"))] = "金額を入力してください"
        
        if name and price:
            amt = int(float(str(price)))
            details.append(f"{name}({amt:,}円)")
            prices.append(f"{amt:,}円")
            total += amt

    if errors:
        ack(response_action="errors", errors=errors)
        return

    ack()

    final_data = {
        "日付": view_state["date_block"]["date_selection"]["selected_date"].replace("-", "/"),
        "種類": (view_state.get("category", {}).get("value", {}).get("selected_option") or {}).get("text", {}).get("text", "その他"),
        "セクション": (view_state.get("section_block", {}).get("value", {}).get("selected_option") or {}).get("text", {}).get("text", ""),
        "内容": " / ".join(details), 
        "内訳": " + ".join(prices), 
        "金額": f"¥{total:,}",
        "支払者": view_state.get("payer", {}).get("value", {}).get("value", ""),
        "精算": "〇" if (view_state.get("settlement", {}).get("value", {}).get("selected_option") or {}).get("value") == "true" else "✕"
    }

    def save():
        from services.sheet_service import add_expenditure_entry
        if add_expenditure_entry(final_data):
            client.chat_postMessage(channel=user_id, text=f"✅ 支出の記帳が完了しました: {final_data['内容']} ¥{total:,}")
        else:
            client.chat_postMessage(channel=user_id, text="⚠️ 保存に失敗しました。")
    
    threading.Thread(target=save).start()


def handle_receipt_input(ack, body, client):
    """
    画像認識モーダルの「送信」が押された時の処理
    """
    try:
        view_state = body["view"]["state"]["values"]
        user_id = body["user"]["id"]
        errors = {}

        # バリデーション
        if "receipt" not in view_state or not view_state["receipt"]["file"]["files"]:
            errors["receipt"] = "レシート画像をアップロードしてください"

        if errors:
            ack(response_action="errors", errors=errors)
            return

        # --- データ抽出 ---
        # 種類 (必須)
        category_opt = view_state.get("category", {}).get("value", {}).get("selected_option")
        category = category_opt["text"]["text"] if category_opt else "その他"

        # セクション (任意: 入力なければ空文字)
        section_opt = view_state.get("section_block", {}).get("value", {}).get("selected_option")
        section = section_opt["text"]["text"] if section_opt else ""

        # 支払者 (必須)
        payer = view_state.get("payer", {}).get("value", {}).get("value", "").strip()

        # 精算 (任意: true/false/null)
        settlement_opt = view_state.get("settlement", {}).get("value", {}).get("selected_option")
        settlement = settlement_opt["value"] if settlement_opt else "null"

        metadata = {
            "category": category,
            "section": section,
            "payer": payer,
            "settlement": settlement
        }

        file_id = view_state["receipt"]["file"]["files"][0]["id"]

        ack() # 承認してモーダルを閉じる

        client.chat_postMessage(channel=user_id, text="📥 レシートを受け取りました。解析を開始します。")

        threading.Thread(
            target=process_receipt_workflow,
            args=(client, user_id, file_id, metadata),
            daemon=True
        ).start()

    except Exception as e:
        logger.error(f"Error in handle_receipt_input: {e}")
        try: ack()
        except: pass


def handle_membership_fee_submission(ack, body, client):
    try:
        view_state = body["view"]["state"]["values"]
        user_id = body["user"]["id"]
        
        selected_user = view_state.get("user_selection_block", {}).get("user_action", {}).get("selected_user")
        manual_name = view_state.get("manual_name_block", {}).get("name_action", {}).get("value")

        if not selected_user and not manual_name:
            ack(response_action="errors", errors={"manual_name_block": "名前を入力または選択してください"})
            return

        ack()

        search_name = manual_name
        display_name = manual_name
        
        # ユーザー選択を優先
        if not manual_name and selected_user:
            res = client.users_info(user=selected_user)
            if res["ok"]:
                search_name = res["user"]["real_name"]
                display_name = f"<@{selected_user}> ({search_name})"

        from services.sheet_service import get_payment_status
        paid_list = get_payment_status(search_name)

        message_blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": "📊 部費支払い状況確認"}},
            {"type": "section", "text": {"type": "mrkdwn", "text": f"対象者: *{display_name}* さん"}},
            {"type": "divider"}
        ]
        
        if not paid_list:
            message_blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"⚠️ *「{search_name}」さんのデータが見つかりませんでした。*"}})
        else:
            history = "\n".join([f"✅ {item}" for item in paid_list])
            message_blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"*支払い済み履歴:*\n{history}"}})

        client.chat_postMessage(channel=user_id, blocks=message_blocks)
    except Exception as e:
        logger.error(f"Membership fee error: {e}")


def handle_other_income_submission(ack, body, client):
    try:
        view_state = body["view"]["state"]["values"]
        user_id = body["user"]["id"]
        data = {
            "日付": view_state["date_block"]["date_selection"]["selected_date"].replace("-", "/"),
            "内容": view_state["content"]["value"]["value"],
            "金額": f"¥{int(view_state['amount']['value']['value']):,}"
        }

        ack()

        from services.sheet_service import add_other_income_entry
        success = add_other_income_entry(data)
        
        client.chat_postMessage(
            channel=user_id, 
            text=f"✅ その他収入を記帳しました: {data['内容']} {data['金額']}" if success else "⚠️ 保存に失敗しました。"
        )
    except Exception as e:
        logger.error(f"Error: {e}")




# ============================================================
# 6. バックグラウンド・ワーカー
# ============================================================


def process_receipt_workflow(client, user_id, file_id, metadata):
    try:
        from services.slack_service import download_slack_file
        from services.openai_service import analyze_receipt
        from services.sheet_service import add_expenditure_entry

        image_content = download_slack_file(client, file_id)
        if not image_content:
            client.chat_postMessage(channel=user_id, text="⚠️ 画像の取得に失敗しました。")
            return

        ai_data = analyze_receipt(image_content)
        if not ai_data:
            client.chat_postMessage(channel=user_id, text="⚠️ レシートの解析に失敗しました。")
            return

        settlement_label = "〇" if metadata["settlement"] == "true" else "✕" if metadata["settlement"] == "false" else ""
        
        final_entry = {
            "日付": ai_data.get("日付", ""),
            "種類": metadata["category"],
            "セクション": metadata["section"],
            "内容": ai_data.get("内容", ""),
            "内訳": ai_data.get("内訳", ""),
            "金額": f"¥{int(ai_data.get("金額", "")):,}",
            "支払者": metadata["payer"],
            "精算": settlement_label
        }
        
        success = add_expenditure_entry(final_entry)
        if success:
            client.chat_postMessage(
                channel=user_id, 
                text=f"✅ 画像認識での記帳が完了しました：{final_entry['内容']} {final_entry['内訳']} {final_entry['金額']}"
            )
        else:
            client.chat_postMessage(channel=user_id, text="⚠️ 保存に失敗しました。")

    except Exception as e:
        logger.error(f"Workflow error: {e}")
        client.chat_postMessage(channel=user_id, text=f"❌ 処理エラーが発生しました: {e}")