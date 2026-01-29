import logging
from features.accounting_feature import get_receipt_input_view_from_shortcut
from config import ACCOUNTING_USERS 

logger = logging.getLogger(__name__)

def handle_receipt_shortcut(ack, body, client):
    ack()
    try:
        user_id = body["user"]["id"]
        
        if user_id not in ACCOUNTING_USERS:
            client.chat_postEphemeral(
                channel=body["channel"]["id"],
                user=user_id,
                text="⚠️ この機能は会計係専用です。"
            )
            return

        message = body.get("message", {})
        files = message.get("files", [])
        
        if not files:
            client.chat_postEphemeral(
                channel=body["channel"]["id"],
                user=user_id,
                text="⚠️ メッセージにファイルが見つかりません。"
            )
            return

        file_id = files[0]["id"]

        client.views_open(
            trigger_id=body["trigger_id"],
            view=get_receipt_input_view_from_shortcut(file_id)
        )
    except Exception:
        logger.exception("Handle Receipt Shortcut Error")