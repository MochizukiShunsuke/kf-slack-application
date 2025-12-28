import re

def handle_rag(event, say, client):
    from services.rag_service import run_rag_flow
    print("[DEBUG] handle_rag called")

    channel_id = event["channel"]
    ts = event["ts"]
    text = event.get("text", "")

    try:
        # 1.処理中リアクション追加
        client.reactions_add(
            channel=channel_id,
            timestamp=ts,
            name="処理中"
        )

        # 2.メンション除去
        query = re.sub(r"<@.*?>", "", text).strip()

        if not query:
            say("質問内容を入力してください。", thread_ts=ts)
            return

        print(f"[DEBUG] Running RAG flow for query: {query}")

        # 3.RAG実行
        answer = run_rag_flow(query)

        # 4.処理中リアクション削除
        client.reactions_remove(
            channel=channel_id,
            timestamp=ts,
            name="処理中"
        )

        # 5.回答送信
        say(answer, thread_ts=ts)
        print("[DEBUG] RAG answer sent successfully.")

    except Exception as e:
        print(f"[ERROR] RAG Error: {e}")
        import traceback
        traceback.print_exc()
        say(
            "⚠️ RAG処理中にエラーが発生しました。",
            thread_ts=ts
        )
