import json
import logging
import re
from datetime import datetime, timedelta, timezone
from google.cloud import tasks_v2

from config import (
    GOOGLE_CLOUD_PROJECT,
    REGION,
    ACTIVITY_REPORT_QUEUE_NAME,
    SERVICE_URL,
    SERVICE_ACCOUNT_EMAIL
)

logger = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9), "JST")

def handle_activity_report_from_command(ack, command, client, say):
    ack()

    try:
        user_id = command["user_id"]
        channel_id = command["channel_id"]
        text = command.get("text", "").strip()

        target_label = ""
        match = re.search(r"(\d{4})年度(\d{1,2})月", text)

        if match:
            target_label = match.group(0)
        else:
            now = datetime.now(JST)
            month = now.month

            if month >= 10:
                year = now.year + 1
            else:
                year = now.year
                
            target_label = f"{year}年度{month}月"

        say(f"<@{user_id}> 承知しました。「{target_label}」として近況活動報告書の作成を開始します... ⏳")

        if not SERVICE_URL:
            logger.error("SERVICE_URL is not set.")
            return

        client_tasks = tasks_v2.CloudTasksClient()
        
        parent = client_tasks.queue_path(GOOGLE_CLOUD_PROJECT, REGION, ACTIVITY_REPORT_QUEUE_NAME)

        payload = {
            "type": "generation",
            "user_id": user_id,
            "channel_id": channel_id,
            "target_month": target_label
        }

        task = {
            "http_request": {
                "http_method": tasks_v2.HttpMethod.POST,
                "url": f"{SERVICE_URL}/jobs/activity-report",
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(payload).encode(),
                "oidc_token": {"service_account_email": SERVICE_ACCOUNT_EMAIL}
            }
        }

        client_tasks.create_task(request={"parent": parent, "task": task})
        logger.info(f"Task created for {target_label}")

    except Exception as e:
        logger.exception("Failed to handle activity report command")
        say(f"<@{user_id}> ❌ エラーが発生しました: {e}")