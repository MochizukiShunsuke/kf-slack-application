import logging
from services.sheet_service import get_all_members, get_trigger_rules

logger = logging.getLogger(__name__)

def register_message_router(slack_app):
    print("message_router.py registered")

    @slack_app.event("message")
    def handle_keyword_trigger(event, context, say):
        try:
            # 1. 不要なメッセージをスキップ（bot自身の発言など）
            if event.get("bot_id") is not None:
                return

            text = event.get("text", "").replace("＠", "@")
            if not text:
                return
            
            bot_user_id = context.get("bot_user_id")
            if bot_user_id and f"<@{bot_user_id}>" in text:
                return
            
            if text.strip().startswith("/"):
                return
            
            current_channel = event["channel"]
            thread_ts = event.get("ts")

            # 2. ルール取得とエラー判定
            rules = get_trigger_rules()
            if rules is None:
                logger.error("キーワードルールの取得に失敗しました")
                return

            # 3. 反応すべきキーワードがあるかチェック
            valid_triggers = []
            for trigger, allowed_channels in rules.items():
                if trigger in text:
                    if "ALL" in allowed_channels or current_channel in allowed_channels:
                        valid_triggers.append(trigger)

            if not valid_triggers:
                return

            # 4. メンバーリスト取得とエラー判定
            members = get_all_members()
            if members is None:
                logger.error("メンバーリストの取得に失敗しました")
                return

            # 5. メンション対象の抽出
            target_ids = set()
            for member in members:
                for tag in member.get("tags", []):
                    if tag in valid_triggers:
                        target_ids.add(member["id"])

            if not target_ids:
                # キーワードには反応したが、担当タグを持つメンバーがいない場合
                logger.info(f"キーワード '{valid_triggers}' に反応しましたが、該当するタグを持つメンバーがいません。")
                return

            # 6. メンション送信
            mention_text = " ".join(f"<@{uid}>" for uid in target_ids)
            trigger_msg = "・".join(valid_triggers)
            say(
                f"{mention_text}\n"
                f"(キーワード: {trigger_msg} に反応しました)",
                thread_ts=thread_ts,
            )
        except Exception:
            logger.exception("Handle Keyword Trigger Error")
            return