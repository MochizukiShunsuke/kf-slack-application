import requests
import os

def download_slack_file(client, file_id):
    try:
        file_info = client.files_info(file=file_id)
        url = file_info['file']['url_private_download']
        token = os.environ.get("SLACK_BOT_TOKEN")
        
        response = requests.get(url, headers={'Authorization': f'Bearer {token}'})
        if response.status_code == 200:
            return response.content
        return None
    except Exception as e:
        print(f"File Download Error: {e}")
        return None