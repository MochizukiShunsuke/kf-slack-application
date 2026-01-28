from config import RAG_CHANNEL_ID, ALLOWED_MENTION_CHANNELS
from listeners.rag_listener import handle_rag_from_app_mention

<<<<<<< HEAD
def register_app_mention_router(app):

    @app.event("app_mention")
=======
def register_app_mention_router(slack_app):

    @slack_app.event("app_mention")
>>>>>>> 6146bfa (Release v1.5.0 : PC & overall reservation and Zoom function)
    def handle_app_mention(event, say, client):
        channel_id = event["channel"]
        ts = event["ts"]
        
        if channel_id in ALLOWED_MENTION_CHANNELS:
            if channel_id == RAG_CHANNEL_ID:
                handle_rag_from_app_mention(event, say, client)
            # elif channel_id == other_CHANNEL_ID:
            return
        
        links = ", ".join([f"<#{c_id}>" for c_id in ALLOWED_MENTION_CHANNELS])
        say(
            text=f"⚠️ このチャンネルでBotにmentionできません。\n可能なチャンネルはこちらです：{links}",
            thread_ts=ts
        )