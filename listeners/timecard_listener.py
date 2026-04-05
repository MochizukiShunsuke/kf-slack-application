import threading
import logging
from datetime import datetime
from features.timecard_feature import get_timecard_view
from services.sheet_service import add_timecard_log

logger = logging.getLogger(__name__)

def handle_timecard_command(ack, body, client):
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view=get_timecard_view()
    )

def handle_timecard_submission(ack, body, client):
    view_state = body["view"]["state"]["values"]
    user_id = body["user"]["id"]
    user_name = body["user"]["name"]
    
    ack()

    action = view_state["action_block"]["action_select"]["selected_option"]["value"]
    department = view_state["dept_block"]["dept_select"]["selected_option"]["text"]["text"]
    work_detail = view_state["work_block"]["work_input"]["value"] or ""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    record = [timestamp, user_id, user_name, action, department, work_detail]

    def save():
        try:
            if add_timecard_log(record):
                is_checkin = (action == "CHECK_IN")
                status_label = "出勤" if is_checkin else "退勤"

                client.chat_postMessage(
                    channel=user_id, 
                    text="*タイムカードを記録しました*",
                    blocks=[
                        {
                            "type": "section",
                            "text": {
                                "type": "mrkdwn", 
                                "text": f"*{status_label}を記録しました*"
                            }
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*時刻:*\n{timestamp}"},
                                {"type": "mrkdwn", "text": f"*セクション:*\n{department}"}
                            ]
                        },
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": f"*作業内容:*\n{work_detail or '（未入力）'}"}
                        }
                    ]
                )
            else:
                client.chat_postMessage(channel=user_id, text="⚠️ スプレッドシートへの保存に失敗しました。管理者に確認してください。")
        except Exception:
            logger.exception("Save Thread (Timecard) Error")
            client.chat_postMessage(channel=user_id, text="❌ 記録処理中にエラーが発生しました。")

    threading.Thread(target=save).start()