from config import RAG_CHANNEL_ID, ALLOWED_MENTION_CHANNELS
from listeners.rag import handle_rag

def register_app_mention_router(app):

    @app.event("app_mention")
    def handle_app_mention(event, say, client):
        channel_id = event["channel"]
        ts = event["ts"]

        # 1. 許可されたチャンネルか判定
        if channel_id in ALLOWED_MENTION_CHANNELS:
            if channel_id == RAG_CHANNEL_ID:
                handle_rag(event, say, client)
            # elif channel_id == other_CHANNEL_ID:
            return

        # 2. 許可されていない場合：利用可能なチャンネルを一覧にして通知
        links = ", ".join([f"<#{c_id}>" for c_id in ALLOWED_MENTION_CHANNELS])
        
        say(
            text=f"⚠️ このチャンネルでBotにmentionできません。\n可能なチャンネルはこちらです：{links}",
            thread_ts=ts
        )