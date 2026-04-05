import requests
import os
from slack_sdk import WebClient
import logging

logger = logging.getLogger(__name__)

def download_slack_file(client, file_id):
    print("slack_service.download_slack_file...")
    try:
        file_info = client.files_info(file=file_id)
        url = file_info['file']['url_private_download']
        token = os.environ.get("SLACK_BOT_TOKEN")
        
        response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
        if response.status_code == 200:
            return response.content

        logger.error(f"Slack Download API Error: {response.status_code}")
        return None 
    except Exception:
        logger.exception("Download Slack File Error")
        return None

def send_slack_message(channel, text, blocks=None, thread_ts=None):
    print("slack_service.send_slack_message...")
    try:
        token = os.environ.get("SLACK_BOT_TOKEN")
        client = WebClient(token=token)
        valid_thread_ts = thread_ts if thread_ts and str(thread_ts).strip() else None

        return client.chat_postMessage(
            channel=channel,
            text=text,
            blocks=blocks,
            thread_ts=valid_thread_ts
        )
    except Exception as e:
        error_code = getattr(e, "response", {}).get("error", "unknown_error")
        logger.error(f"Send Slack Message Error: {error_code} (ts: {thread_ts})")
        return None
    
def upload_slack_file(channel_id, file_content, title, filename, comment=None):
    print("slack_service.upload_slack_file...")
    try:
        token = os.environ.get("SLACK_BOT_TOKEN")
        client = WebClient(token=token)
        
        response = client.files_upload_v2(
            channel=channel_id,
            file=file_content,
            title=title,
            filename=filename,
            initial_comment=comment
        )
        return response
    except Exception:
        logger.exception("Upload Slack File Error")
        return None
    
def publish_home_view(user_id, blocks):
    print("slack_service.publish_home_view...")
    try:
        token = os.environ.get("SLACK_BOT_TOKEN")
        client = WebClient(token=token)
        client.views_publish(
            user_id=user_id,
            view={
                "type": "home",
                "blocks": blocks
            }
        )
        return True
    except Exception:
        logger.exception("Publish Home View Error")
        return False