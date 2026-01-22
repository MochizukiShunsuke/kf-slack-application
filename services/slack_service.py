import requests
import os
from slack_sdk import WebClient
import logging

logger = logging.getLogger(__name__)

def download_slack_file(client, file_id):
    try:
        file_info = client.files_info(file=file_id)
        url = file_info['file']['url_private_download']
        token = os.environ.get("SLACK_BOT_TOKEN")
        
        response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
        if response.status_code == 200:
            return response.content
        # ステータスコード200以外（Slack側のエラー）の場合
        logger.error(f"Slack Download API Error: {response.status_code}")
        return None 
    except Exception:
        logger.exception("Download Slack File Error")
        return None
    
def send_slack_message(channel, text, blocks=None, thread_ts=None):
    try:
        token = os.environ.get("SLACK_BOT_TOKEN")
        client = WebClient(token=token)
        return client.chat_postMessage(
            channel=channel,
            text=text,
            blocks=blocks,
            thread_ts=thread_ts
        )
    except Exception:
        logger.exception("Send Slack Message Error")
        return None