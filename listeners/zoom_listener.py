import datetime
import os
import threading
import logging
from services.openai_service import summarize_text
from services.slack_service import send_slack_message
from services.firestore_service import db
def handle_ingest(request):
    """Zoom等からの文字起こしデータを受け取り、Firestoreに保存する"""
    try:
        data = request.json
        meeting_id = data.get("meeting_id", f"meeting_{datetime.date.today().isoformat()}")
        transcript_text = data.get("text")

        if not transcript_text:
            return {"status": "error", "message": "No text provided"}, 400
        
        db.collection("meetings").document(meeting_id).collection("transcript").add({
            "text": transcript_text,
            "timestamp": datetime.datetime.now(datetime.timezone.utc)
        })
        return {"status": "success"}, 200
    except Exception as e:
        logging.error(f"Ingest Error: {e}")
        return {"status": "error", "message": str(e)}, 500

def handle_meeting_summary_from_command(ack, command, context):
    """Slackコマンドを受け取り、要約処理をバックグラウンドで開始する"""
    ack("議事録の要約を開始します。完了次第、このチャンネルに投稿します。")
    thread = threading.Thread(target=process_summary_background, args=(command,))
    thread.start()

def process_summary_background(command):
    """バックグラウンドでFirestoreから読み取り、要約して送信する"""
    try:
        meeting_id = command.get("text") or f"meeting_{datetime.date.today().isoformat()}"
        channel_id = command.get("channel_id")
        
        docs = db.collection("meetings").document(meeting_id).collection("transcript").order_by("timestamp").stream() #
        full_text = "\n".join([doc.to_dict().get("text") for doc in docs])

        if not full_text:
            send_slack_message(channel_id, f"⚠️ 会議データ `{meeting_id}` は見つかりませんでした。")
            return
        
        summary = summarize_text(full_text)
        send_slack_message(channel_id, f"📢 *会議要約 ({meeting_id})*\n\n{summary}")
    except Exception as e:
        logging.error(f"Background Summary Error: {e}")