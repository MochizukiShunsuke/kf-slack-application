from features.rag_feature import get_rag_response_blocks
from services.slack_service import send_slack_message
import logging

logger = logging.getLogger(__name__)

def handle_rag_submission_ack(ack):
    ack()

def handle_rag_submission_lazy(view, body):
    user_question = view["state"]["values"]["question_block"]["question_input"]["value"]
    user_id = body["user"]["id"]
    try:
        send_slack_message(channel=user_id, text=f"🔍 「{user_question}」についてお調べしています...")
        answer_blocks = get_rag_response_blocks(user_question)
        send_slack_message(
            channel=user_id,
            text=f"AI回答: {user_question}",
            blocks=answer_blocks
        )
    except Exception:
        logger.exception("Handle Rag Submission Lazy Error")
        send_slack_message(channel=user_id, text=f"⚠️ 検索エラーです。もう一度やり直すか責任者に問い合わせてください。")
        return None