import os
import logging
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler
from google.cloud import firestore
from flask_cors import CORS

# ルーター
from routers.message_router import register_message_router
from routers.command_router import register_command_router
from routers.app_mention_router import register_app_mention_router
from routers.view_router import register_view_router
from routers.shortcut_router import register_shortcut_router
from routers.zoom_router import register_zoom_router

# リスナー
from listeners.jobs_listener import handle_activity_report_job

# サービス
from services.openai_service import summarize_text

logging.basicConfig(level=logging.INFO)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    process_before_response=True 
)

def register_listeners(app, flask_app, db):
    register_message_router(app)
    register_command_router(app)
    register_app_mention_router(app)
    register_view_router(app)
    register_shortcut_router(app)
    register_zoom_router(flask_app, db)

flask_app = Flask(__name__)
CORS(flask_app)
handler = SlackRequestHandler(app)
db = firestore.Client(database="zoom-logs")

@app.middleware
def inject_db(context, next):
    context["db"] = db
    next()

register_listeners(app, flask_app, db)

@flask_app.route("/ping", methods=["GET"])
def ping():
    return "ok", 200

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    retry_num = request.headers.get("x-slack-retry-num")
    if retry_num and retry_num != "0":
        return "OK"
    return handler.handle(request)

@flask_app.route("/jobs/activity-report", methods=["POST"])
def activity_report_job_route():
    return handle_activity_report_job()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)