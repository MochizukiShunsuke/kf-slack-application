from features.accounting_feature import (
    get_receipt_input_view, get_manual_expense_view, 
    get_membership_fee_view, get_other_income_view,
    process_receipt_workflow
)
from services.sheet_service import add_expenditure_entry
from services.sheet_service import get_payment_status
from services.sheet_service import add_other_income_entry
import threading
import logging

logger = logging.getLogger(__name__)

def handle_menu_selection(ack, body, client):
    view_state = body["view"]["state"]["values"]
    user_id = body["user"]["id"]
    
    try:
        selected_menu = view_state["menu_block"]["menu_action"]["selected_option"]["value"]

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
    except Exception:
        ack()
        logger.exception("Handle Menu Selection Error")
        return


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
    except Exception:
        logger.exception("Handle Modal Update Error")
        return

def handle_manual_expense_submission(ack, body, client):
    try:
        view_state = body["view"]["state"]["values"]
        metadata = body["view"].get("private_metadata", "1_0")
        item_count = int(metadata.split("_")[0])
        user_id = body["user"]["id"]
        details, prices, total, errors = [], [], 0, {}
        
        for i in range(item_count):
            name, price = None, None
            
            for block_id, actions in view_state.items():
                if block_id.startswith(f"item_name_{i}_"):
                    name = actions.get("name_action", {}).get("value")
                if block_id.startswith(f"item_amt_{i}_"):
                    price = actions.get("price_action", {}).get("value")
            
            if not name: 
                block_id = next((k for k in view_state if k.startswith(f"item_name_{i}_")), None)
                if block_id: errors[block_id] = "品目名を入力してください"
            if not price: 
                block_id = next((k for k in view_state if k.startswith(f"item_amt_{i}_")), None)
                if block_id: errors[block_id] = "金額を入力してください"
            
            if name and price:
                try:
                    amt = int(float(str(price)))
                    details.append(f"{name}({amt:,}円)")
                    prices.append(f"{amt:,}円")
                    total += amt
                except (ValueError, TypeError):
                    block_id = next((k for k in view_state if k.startswith(f"item_amt_{i}_")), None)
                    if block_id: errors[block_id] = "数値で入力してください"
        
        if errors:
            ack(response_action="errors", errors=errors)
            return
        ack()
        
        final_data = {
            "日付": view_state.get("date_block", {}).get("date_selection", {}).get("selected_date", "").replace("-", "/"),
            "種類": (view_state.get("category", {}).get("value", {}).get("selected_option") or {}).get("text", {}).get("text", "その他"),
            "セクション": (view_state.get("section_block", {}).get("value", {}).get("selected_option") or {}).get("text", {}).get("text", ""),
            "内容": " / ".join(details), 
            "内訳": " + ".join(prices), 
            "金額": f"¥{total:,}",
            "支払者": view_state.get("payer", {}).get("value", {}).get("value", ""),
            "精算": "〇" if (view_state.get("settlement", {}).get("value", {}).get("selected_option") or {}).get("value") == "true" else "✕"
        }
        
        def save():
            try:
                #from services.sheet_service import add_expenditure_entry
                if add_expenditure_entry(final_data):
                    client.chat_postMessage(channel=user_id, text=f"✅ 支出の記帳が完了しました: {final_data['内容']} ¥{total:,}")
                else:
                    client.chat_postMessage(channel=user_id, text="⚠️ 保存に失敗しました。スプレッドシートの権限や設定を確認してください。")
            except Exception:
                
                logger.exception("Save Thread (Manual Expense) Error")
                client.chat_postMessage(channel=user_id, text="⚠️ 保存処理中に致命的なエラーが発生しました。")
        threading.Thread(target=save).start()
    except Exception:
        logger.exception("Handle Manual Expense Submission Error")
        return


def handle_receipt_input(ack, body, client):
    try:
        view_state = body["view"]["state"]["values"]
        user_id = body["user"]["id"]
        errors = {}
        
        if "receipt" not in view_state or not view_state["receipt"]["file"]["files"]:
            errors["receipt"] = "レシート画像をアップロードしてください"
        if errors:
            ack(response_action="errors", errors=errors)
            return
        
        category_opt = view_state.get("category", {}).get("value", {}).get("selected_option")
        category = category_opt["text"]["text"] if category_opt else "その他"
        section_opt = view_state.get("section_block", {}).get("value", {}).get("selected_option")
        section = section_opt["text"]["text"] if section_opt else ""
        payer = view_state.get("payer", {}).get("value", {}).get("value", "").strip()
        settlement_opt = view_state.get("settlement", {}).get("value", {}).get("selected_option")
        settlement = settlement_opt["value"] if settlement_opt else "null"
        metadata = {
            "category": category,
            "section": section,
            "payer": payer,
            "settlement": settlement
        }
        file_id = view_state["receipt"]["file"]["files"][0]["id"]
        ack()
        client.chat_postMessage(channel=user_id, text="📥 レシートを受け取りました。解析を開始します。")
        threading.Thread(
            target=process_receipt_workflow,
            args=(client, user_id, file_id, metadata),
            daemon=True
        ).start()
    except Exception:
        logger.exception("Handle Receipt Input Error")
        return


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
        
        # ユーザー選択優先
        if not manual_name and selected_user:
            res = client.users_info(user=selected_user)
            if res["ok"]:
                search_name = res["user"]["real_name"]
                display_name = f"<@{selected_user}> ({search_name})"

        #from services.sheet_service import get_payment_status
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
    except Exception:
        logger.exception("Handle Membership Fee Submission Error")
        return


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
        #from services.sheet_service import add_other_income_entry
        success = add_other_income_entry(data)
        
        client.chat_postMessage(
            channel=user_id, 
            text=f"✅ その他収入を記帳しました: {data['内容']} {data['金額']}" if success else "⚠️ 保存に失敗しました。"
        )
    except Exception:
        logger.exception("Handle Other Income Submission Error")
        return