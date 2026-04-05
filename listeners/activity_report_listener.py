import os
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
    SERVICE_ACCOUNT_EMAIL,
    ACTIVITY_REPORT_MESSAGE_FOLDER_ID,
    ACTIVITY_PICTURE_FOLDER_ID
)

from services.drive_service import (
    find_folder_by_name, 
    upload_text_as_docx, 
    get_user_draft_text, 
    upload_image_from_url,
    upload_docx_from_url
)

from services.sheet_service import (
    get_member_name_from_slack_id, 
    get_assignee_number
)

from features.app_home_feature import get_current_nendo_month


logger = logging.getLogger(__name__)
JST = timezone(timedelta(hours=9), "JST")

def handle_activity_report_from_command(ack, command, say):
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
        say(f"<@{user_id}> 承知しました。「{target_label}」の近況活動報告書の作成を開始します... ⏳")

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


def handle_open_report_modal_ack(ack):
    ack()

def handle_open_report_modal_lazy(body, client):
    trigger_id = body["trigger_id"]
    now = datetime.now()
    month = now.month
    if month >= 10:
        year = now.year + 1
    else:
        year = now.year
        
    target_month = f"{year}年度{month}月"
    modal_view = {
        "type": "modal",
        "callback_id": "submit_report_view",
        "title": {"type": "plain_text", "text": "提出フォーム"},
        "submit": {"type": "plain_text", "text": "送信"},
        "close": {"type": "plain_text", "text": "閉じる"},
        "private_metadata": target_month,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*{target_month}* の活動報告を作成します。"
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "input",
                "block_id": "text_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "📝 近活原稿 (担当者のみ)"},
                "element": {
                    "type": "file_input",
                    "action_id": "content",
                    "filetypes": ["docx"],
                    "max_files": 1
                }
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "📷 *活動写真のアップロード (誰でもOK)*\n写真を提出する場合は、以下の *番号* と *説明* を必ず入力してください。"
                }
            },
            {
                "type": "input",
                "block_id": "number_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "Activity No. (近活に挿入する順番)"},
                "element": {
                    "type": "static_select",
                    "action_id": "activity_num",
                    "placeholder": {"type": "plain_text", "text": "番号を選択"},
                    "options": [
                        {"text": {"type": "plain_text", "text": "1"}, "value": "1"},
                        {"text": {"type": "plain_text", "text": "2"}, "value": "2"},
                        {"text": {"type": "plain_text", "text": "3"}, "value": "3"},
                        {"text": {"type": "plain_text", "text": "4"}, "value": "4"},
                        {"text": {"type": "plain_text", "text": "5"}, "value": "5"},
                        {"text": {"type": "plain_text", "text": "6"}, "value": "6"}
                    ]
                }
            },
            {
                "type": "input",
                "block_id": "desc_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "写真の説明"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "photo_desc",
                    "placeholder": {"type": "plain_text", "text": "例: DRの様子、集合写真など"}
                }
            },
            {
                "type": "input",
                "block_id": "photo_block",
                "optional": True,
                "label": {"type": "plain_text", "text": "写真を選択 (1枚ずつ)"},
                "element": {
                    "type": "file_input",
                    "action_id": "photo",
                    "filetypes": ["jpg", "jpeg", "png"],
                    "max_files": 1
                }
            }
        ]
    }
    client.views_open(trigger_id=trigger_id, view=modal_view)

def handle_view_submission_ack(ack):
    ack()

def handle_view_submission_lazy(body, view, client, logger):
    user_id = body["user"]["id"]
    target_month = view["private_metadata"] 
    values = view["state"]["values"]
    docx_files = values["text_block"]["content"].get("files")
    activity_num = values["number_block"]["activity_num"]["selected_option"]
    photo_desc = values["desc_block"]["photo_desc"]["value"]
    photo_files = []
    if "photo_block" in values and "photo" in values["photo_block"]:
        if values["photo_block"]["photo"]["files"]:
            photo_files = values["photo_block"]["photo"]["files"]

    sheet_name = get_member_name_from_slack_id(user_id)
    if sheet_name:
        user_name = sheet_name
    else:
        user_info = client.users_info(user=user_id)
        user_name = user_info["user"]["real_name"] or user_info["user"]["name"]

    number_prefix = get_assignee_number(target_month, user_name)
    token = os.environ.get("SLACK_BOT_TOKEN")
    messages = []

    if docx_files or photo_files:
        client.chat_postMessage(channel=user_id, text="📤 保存を開始しました...")

    try:
        target_msg_folder = find_folder_by_name(ACTIVITY_REPORT_MESSAGE_FOLDER_ID, target_month)
        target_pic_folder = find_folder_by_name(ACTIVITY_PICTURE_FOLDER_ID, target_month)
        
        if not target_msg_folder or not target_pic_folder:
            client.chat_postMessage(
                channel=user_id, 
                text=f"❌ Driveに「{target_month}」のフォルダが見つかりませんでした。\n親フォルダを確認してください。"
            )
            return

        if docx_files:
            file_info = docx_files[0]

            filename = f"{number_prefix}_{target_month}近活原稿_{user_name}.docx"

            dl_url = file_info["url_private_download"]

            upload_docx_from_url(target_msg_folder, filename, dl_url, token)
            
            messages.append(f"📝 原稿を保存しました")

        if messages:
            client.chat_postMessage(
                channel=user_id, 
                text=f"✅ *{target_month}* の提出が完了しました！\n" + "\n".join(messages)
            )
        else:
            client.chat_postMessage(channel=user_id, text="⚠️ 送信内容が空でした。")

    except Exception as e:
        logger.exception("Submission Error")
        client.chat_postMessage(channel=user_id, text=f"❌ 保存中にエラーが発生しました: {str(e)}")