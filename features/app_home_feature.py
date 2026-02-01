import logging
from datetime import datetime, timedelta, timezone
from services.slack_service import publish_home_view

logger = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9), "JST")

def get_current_nendo_month():
    now = datetime.now(JST)
    month = now.month
    if month >= 10:
        year = now.year + 1
    else:
        year = now.year
    return f"{year}年度{month}月"

def render_app_home(user_id):
    logger.info(f"Rendering App Home for {user_id}")
    
    target_label = get_current_nendo_month()

    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "🏎️ 金沢大学フォーミュラ研究会 Bot", "emoji": True}
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"お疲れ様です！\n現在は *【{target_label}】* の活動報告期間です。"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": "👇 以下のボタンから原稿・写真の提出、編集が可能です。"}
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "📝 原稿・写真を提出する", "emoji": True},
                    "style": "primary",
                    "action_id": "open_report_modal_action"
                }
            ]
        },
        {"type": "divider"}
    ]
    
    publish_home_view(user_id, blocks)