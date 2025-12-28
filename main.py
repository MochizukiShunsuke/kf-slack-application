import os
import logging
from flask import Flask, request
from slack_bolt import App
from slack_bolt.adapter.flask import SlackRequestHandler


logging.basicConfig(level=logging.INFO)


def register_listeners(app):
    from listeners.message_router import register_message_router
    from listeners.command_router import register_command_router
    from listeners.app_mention_router import register_app_mention_router
    from listeners.view_router import register_view_router

    register_message_router(app)
    register_command_router(app)
    register_app_mention_router(app)
    register_view_router(app)

app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET"),
    process_before_response=True 
)

# 登録関数を呼び出し
register_listeners(app)

# Flask アダプター
flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def slack_events():
    retry_num = request.headers.get("x-slack-retry-num")
    if retry_num and retry_num != "0":
        return "OK"
    return handler.handle(request)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host="0.0.0.0", port=port)