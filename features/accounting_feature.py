from services.slack_service import download_slack_file
from services.openai_service import analyze_receipt
from services.sheet_service import add_expenditure_entry
import json
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


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

# --- UI生成ロジック ---

def get_receipt_input_view_from_command():
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

###試作###
def get_receipt_input_view_from_shortcut(file_id: str):
    """メッセージショートカット専用：添付ファイルIDを引き継いでモーダルを表示"""
    return {
        "type": "modal",
        "callback_id": "accounting_receipt_input_shortcut",
        "title": {"type": "plain_text", "text": "支出入力(レシート画像認識)"},
        "submit": {"type": "plain_text", "text": "送信"},
        "close": {"type": "plain_text", "text": "戻る"},
        "private_metadata": json.dumps({
            "file_id": file_id
        }),
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📎 投稿元に添付されたファイルを使用します"
                }
            },
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
            "private_metadata": f"{item_count}_{reset_id}",
            "title": {"type": "plain_text", "text": "支出入力(手動)"},
            "submit": {"type": "plain_text", "text": "送信"},
            "close": {"type": "plain_text", "text": "戻る"},
            "blocks": blocks
        }

def get_membership_fee_status_view():
    return {
        "type": "modal",
        "callback_id": "membership_fee_status_submission",
        "title": {"type": "plain_text", "text": "部費支払い確認"},
        "submit": {"type": "plain_text", "text": "確認"},
        "close": {"type": "plain_text", "text": "戻る"},
        "blocks": [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "確認したい部員を選択してください。"}
            },
            {
                "type": "input",
                "block_id": "user_selection_block",
                "label": {"type": "plain_text", "text": "部員を選択"},
                "element": {
                    "type": "users_select",
                    "placeholder": {"type": "plain_text", "text": "ユーザーを選択"},
                    "action_id": "user_action"
                }
            }
        ]
    }

def get_membership_fee_payment_name_view():
    """部費支払い入力(1/2)：Slackメンバー選択のみ"""
    return {
        "type": "modal",
        "callback_id": "membership_fee_payment_name_submission",
        "title": {"type": "plain_text", "text": "部費支払い入力(1/2)"},
        "submit": {"type": "plain_text", "text": "次へ"},
        "close": {"type": "plain_text", "text": "戻る"},
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": "支払った部員を選択してください。"}},
            {
                "type": "input",
                "block_id": "user_selection_block",
                "label": {"type": "plain_text", "text": "部員を選択"},
                "element": {
                    "type": "users_select",
                    "action_id": "user_action",
                    "placeholder": {"type": "plain_text", "text": "ユーザーを選択"}
                }
            }
        ]
    }

def get_membership_fee_payment_data_view(display_name, search_name, unpaid_months, selected_user):
    today = datetime.now().strftime("%Y-%m-%d")
    options = [{"text": {"type": "plain_text", "text": m}, "value": m} for m in unpaid_months]
    
    if not options:
        options = [{"text": {"type": "plain_text", "text": "全ての月が支払い済みです"}, "value": "done"}]

    return {
        "type": "modal",
        "callback_id": "membership_fee_payment_final_submission",
        "private_metadata": f"{search_name}|{selected_user}",
        "title": {"type": "plain_text", "text": "部費支払い入力(2/2)"},
        "submit": {"type": "plain_text", "text": "送信"},
        "blocks": [
            {"type": "section", "text": {"type": "mrkdwn", "text": f"対象者: *{display_name}* さん"}},
            {
                "type": "input", "block_id": "month_block",
                "label": {"type": "plain_text", "text": "支払い対象の月 (複数選択可)"},
                "element": {
                    "type": "multi_static_select",
                    "action_id": "month_select",
                    "options": options,
                    "placeholder": {"type": "plain_text", "text": "月を選択してください"}
                }
            },
            {
                "type": "input", "block_id": "date_block",
                "label": {"type": "plain_text", "text": "支払日"},
                "element": {"type": "datepicker", "action_id": "date_input", "initial_date": today}
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": "※選択したすべての月に対して、上記の日付を「支払日」として一括記録します。"}
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

# --- ワークフローロジック ---

def process_receipt_workflow(client, user_id, file_id, metadata):
    try:
        file_info = client.files_info(file=file_id).get("file", {})
        mimetype = file_info.get("mimetype", "image/jpeg")        
        image_content = download_slack_file(client, file_id)
        if not image_content:
            client.chat_postMessage(channel=user_id, text="⚠️ ファイルの取得に失敗しました。")
            return
        
        ai_data = analyze_receipt(image_content, mimetype=mimetype)
        if not ai_data:
            client.chat_postMessage(channel=user_id, text="⚠️ レシートの解析に失敗しました。")
            return
        
        raw_amount = str(ai_data.get("金額", "0"))
        clean_amount = int(re.sub(r"\D", "", raw_amount) or 0)

        settlement_label = "〇" if metadata["settlement"] == "true" else "✕" if metadata["settlement"] == "false" else ""
        
        final_entry = {
            "日付": ai_data.get("日付", ""),
            "種類": metadata["category"],
            "セクション": metadata["section"],
            "内容": ai_data.get("内容", ""),
            "内訳": ai_data.get("内訳", ""),
            "金額": f"¥{clean_amount:,}",
            "支払者": metadata["payer"],
            "精算": settlement_label
        }
        
        success = add_expenditure_entry(final_entry)
        if success:
            client.chat_postMessage(
                channel=user_id, 
                text=f"✅ 解析と記帳が完了しました：{final_entry['内容']} {final_entry['金額']}"
            )
        else:
            client.chat_postMessage(channel=user_id, text="⚠️ 保存に失敗しました。")

    except Exception as e:
        logger.error(f"Workflow error: {e}")
        client.chat_postMessage(channel=user_id, text=f"❌ 処理エラーが発生しました: {e}")