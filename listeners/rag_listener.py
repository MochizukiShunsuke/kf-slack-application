from features.rag_feature import get_rag_response_blocks
from services.slack_service import send_slack_message
import re
import logging

logger = logging.getLogger(__name__)

def handle_rag_from_app_mention(event, say, client):
    channel_id = event["channel"]
    ts = event["ts"]
    text = event.get("text", "")
    try:
        client.reactions_add(channel=channel_id, timestamp=ts, name="ロード中")
        
        query = re.sub(r"<@.*?>", "", text).strip()
        if not query:
            say(text="質問内容を入力してください。", thread_ts=ts)
            return
        
        answer_blocks = get_rag_response_blocks(query)
        send_slack_message(
            channel=channel_id,
            text=f"AI回答: {query[:20]}...",
            blocks=answer_blocks,
            thread_ts=ts
        )
        client.reactions_remove(channel=channel_id, timestamp=ts, name="ロード中")
    except Exception:
        logger.exception("Handle Rag From App Mention Error")
        send_slack_message(channel=channel_id, text=f"⚠️ 検索エラーです。もう一度やり直すか責任者に問い合わせてください。", thread_ts=ts)
        return None

def handle_rag_from_command(ack, body, client):
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view={
            "type": "modal",
            "callback_id": "rag_question_submission",
            "title": {"type": "plain_text", "text": "レギュレーション回答 -試作-"},
            "blocks": [
                {
                    "type": "input",
                    "block_id": "question_block",
                    "label": {"type": "plain_text", "text": "質問内容"},
                    "element": {
                        "type": "plain_text_input",
                        "action_id": "question_input",
                        "multiline": True
                    }
                }
            ],
            "submit": {"type": "plain_text", "text": "質問する"}
        }
    )