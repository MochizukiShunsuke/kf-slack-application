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

    # ==============================
    # 1. 「完了」リアクションの処理
    # ==============================
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

            # --- 対象の抽出 (PC番号 & overall) ---
            found_items = []
            
            # PC番号 (数字) の抽出
            match_pc = re.search(r"\d+", pc_text)
            if match_pc:
                found_items.append(f"「{match_pc.group()}番」PC")
            
            # overall の抽出 (スペースの有無、大文字小文字を問わない)
            # \s? は「空白文字が0個または1個」という意味
            if re.search(r"over\s?all", pc_text, re.IGNORECASE):
                found_items.append("overall")

            # --- 予約対象が見つからない場合の処理 ---
            if not found_items:
                client.chat_postEphemeral(
                    channel=channel_id,
                    user=user_id,
                    text="⚠️ このメッセージにはPC番号や 'overall' の記載がないため、予約できません。",
                    thread_ts=message_ts
                )
                return

            # 通知用ラベルの作成
            resource_label = " および ".join(found_items)

            # 予約者の確認 (ロジック変更なし)
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

    # =================================
    # 2. 「ご予約承り中」リアクション (既存維持)
    # =================================
    elif reaction == EMOJI_RESERVE:
        # 予約ルールはPC/overall共通のため既存ロジックを維持
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