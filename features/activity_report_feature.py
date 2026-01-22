import datetime
from services.sheet_service import get_activity_report_mentions
from services.slack_service import send_slack_message
from config import ACTIVITY_REPORT_CHANNEL_ID

def run_activity_report_reminder():
    current_month = str(datetime.datetime.now().month)
    mentions = get_activity_report_mentions(current_month)
    
    if not mentions:
        return f"今月({current_month}月)の担当者が見つかりませんでした。"

    target_channel = ACTIVITY_REPORT_CHANNEL_ID
    message = (
        f"近活の原稿を作成し、提出してください\n"
        f"{mentions}\n"
        f"提出期限は25日です"
    )
    response = send_slack_message(channel=target_channel, text=message)
    
    if response:
        return f"Successfully sent to: {mentions}"
    else:
        raise Exception("Slack送信に失敗しました。")