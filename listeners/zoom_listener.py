import datetime
import os
import threading
import logging
from services.openai_service import summarize_text
from services.slack_service import send_slack_message
<<<<<<< HEAD

MEETING_CHANNEL_ID = os.environ.get("MEETING_CHANNEL_ID")

def handle_ingest(request, db):
    try:
        data = request.json
        meeting_id = data.get("meeting_id")
        text = data.get("text")
        
        import logging
        logging.info(f"--- 字幕を受信: {text} (ID: {meeting_id}) ---")
        
        if text:
            db.collection("meetings").document(meeting_id).collection("transcript").add({
                "text": text,
                "timestamp": datetime.datetime.now(datetime.timezone.utc)
            })
            return "OK", 200
        return "Empty text", 400
    except Exception as e:
        logging.error(f"Ingest Error: {e}")
        return str(e), 500

def handle_meeting_summary_from_command(ack, command, context):
    ack("議事録の要約を開始します。完了次第、このチャンネルに投稿します。")
    
    db = context["db"]
    thread = threading.Thread(target=process_summary_background, args=(command, db))
    thread.start()

def process_summary_background(command, db):
    """バックグラウンドで実行される要約・送信処理"""
=======
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
>>>>>>> 6146bfa (Release v1.5.0 : PC & overall reservation and Zoom function)
    try:
        meeting_id = command.get("text") or f"meeting_{datetime.date.today().isoformat()}"
        channel_id = command.get("channel_id")
        
<<<<<<< HEAD
        docs = db.collection("meetings").document(meeting_id).collection("transcript").order_by("timestamp").stream()
=======
        docs = db.collection("meetings").document(meeting_id).collection("transcript").order_by("created_at").stream() #
>>>>>>> 6146bfa (Release v1.5.0 : PC & overall reservation and Zoom function)
        full_text = "\n".join([doc.to_dict().get("text") for doc in docs])

        if not full_text:
            send_slack_message(channel_id, f"⚠️ 会議データ `{meeting_id}` は見つかりませんでした。")
            return
        
        summary = summarize_text(full_text)
<<<<<<< HEAD
        
        send_slack_message(channel_id, f"📢 *会議要約 ({meeting_id})*\n\n{summary}")

=======
        send_slack_message(channel_id, f"📢 *会議要約 ({meeting_id})*\n\n{summary}")
>>>>>>> 6146bfa (Release v1.5.0 : PC & overall reservation and Zoom function)
    except Exception as e:
        logging.error(f"Background Summary Error: {e}")