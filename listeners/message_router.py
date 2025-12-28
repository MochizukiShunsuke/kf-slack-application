import re
from services.sheet_service import get_all_members, get_trigger_rules


def register_message_router(app):
    print("message_router.py (Keyword Trigger) registered")

    @app.event("message")
    def handle_keyword_trigger(event, context, say):
        """
        通常メッセージ用トリガー
        - Botへのメンションは無視
        - Slash Command は無視
        - 会計・RAG 系とは完全に独立
        """

        # 0.Bot自身or他Botの発言は無視
        if event.get("bot_id") is not None:
            return

        text = event.get("text", "")
        if not text:
            return

        # 1.Botメンションは無視（app_mention_routerにまわす）
        bot_user_id = context.get("bot_user_id")
        if bot_user_id and f"<@{bot_user_id}>" in text:
            return

        # 2.Slash Command は無視  
        if text.strip().startswith("/"):
            return

        # 3.スプレッドシートでメンションに変換
        current_channel = event["channel"]
        thread_ts = event.get("ts")
        rules = get_trigger_rules()
        valid_triggers = []

        for trigger, allowed_channels in rules.items():
            if trigger in text:
                if "ALL" in allowed_channels or current_channel in allowed_channels:
                    valid_triggers.append(trigger)

        if not valid_triggers:
            return

        members = get_all_members()
        target_ids = set()

        for member in members:
            for tag in member.get("tags", []):
                if tag in valid_triggers:
                    target_ids.add(member["id"])

        if not target_ids:
            return

        mention_text = " ".join(f"<@{uid}>" for uid in target_ids)
        trigger_msg = "・".join(valid_triggers)

        say(
            f"{mention_text}\n"
            f"(キーワード: {trigger_msg} に反応しました)",
            thread_ts=thread_ts,
        )