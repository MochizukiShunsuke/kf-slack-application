import logging
import re
from slack_sdk.errors import SlackApiError

logger = logging.getLogger(__name__)

EMOJI_DONE = "完了"
EMOJI_RESERVE = "ご予約承り中"

def handle_pc_reaction(event, client, say):
    reaction = event.get("reaction")
    user_id = event.get("user")
    item_user = event.get("item_user")
    channel_id = event.get("item", {}).get("channel")
    message_ts = event.get("item", {}).get("ts")

    if reaction == EMOJI_DONE:
        if user_id != item_user:
            try:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="⚠️ 「完了」リアクションは投稿主（使用者）本人のみ押すことができます。",
                    thread_ts=message_ts
                )
            except SlackApiError as e:
                logger.error(f"Error sending ephemeral message: {e}")
            return

        try:
            response = client.reactions_get(
                channel=channel_id,
                timestamp=message_ts,
                full=True
            )
            message_data = response.get("message", {})
            pc_text = message_data.get("text", "")

            found_items = []

            match_pc = re.search(r"\d+", pc_text)
            if match_pc:
                found_items.append(f"「{match_pc.group()}番」PC")

            if re.search(r"over\s?all", pc_text, re.IGNORECASE):
                found_items.append("overall")

            if not found_items:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="⚠️ このメッセージにはPC番号や 'overall' の記載がないため、予約できません。",
                    thread_ts=message_ts
                )
                return

            resource_label = " および ".join(found_items)

            reactions = message_data.get("reactions", [])
            reserve_users = []
            for r in reactions:
                if r.get("name") == EMOJI_RESERVE:
                    reserve_users = r.get("users", [])
                    break

            if reserve_users:
                first_user = reserve_users[0]
                client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=message_ts,
                    text=(
                        f"<@{first_user}> さん、お待たせしました！\n"
                        f"{resource_label} の利用が完了しました。次にご利用いただけます。"
                    )
                )

        except SlackApiError as e:
            logger.error(f"Error in completion process: {e}")

    elif reaction == EMOJI_RESERVE:
        try:
            response = client.reactions_get(
                channel=channel_id,
                timestamp=message_ts,
                full=True
            )
            message_data = response.get("message", {})
            reactions = message_data.get("reactions", [])
            reserve_info = next((r for r in reactions if r.get("name") == EMOJI_RESERVE), None)
            if not reserve_info:
                return

            users = reserve_info.get("users", [])
            other_users = [u for u in users if u != user_id]
            if other_users:
                client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=message_ts,
                    text=f"<@{user_id}> さん、申し訳ありません。PC/overallの予約は1人までとなっています。先約があるため、予約は無効です。"
                )
        except SlackApiError as e:
            logger.error(f"Error in reservation check: {e}")