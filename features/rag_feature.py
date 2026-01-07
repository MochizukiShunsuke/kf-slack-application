from services.rag_service import run_rag_flow

def get_rag_response_blocks(query_text, chat_history=None):
    response = run_rag_flow(query_text, chat_history)
    
    delimiter = "【参照ソース（関連度スコア順 Top 5）】"
    if delimiter in response:
        idx = response.find(delimiter)
        main_answer = response[:idx].strip()
        reference_part = response[idx:].strip()
    else:
        main_answer = response.strip()
        reference_part = ""
    
    quoted_question = "\n".join([f">{line}" for line in query_text.strip().splitlines()])
    
    answer_blocks = [
        {"type": "divider"},
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*❓ 質問内容*\n{quoted_question}"}
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*💡 AIの回答*\n\n{main_answer}"}
        }
    ]

    if reference_part:
        answer_blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"```\n{reference_part}\n```"}
        })

    answer_blocks.extend([
        {
            "type": "context",
            "elements": [
                {"type": "mrkdwn", "text": "⚠️ *注意:* 最終的な判断は参照元:FSAE Rules 2026を確認してください。"}
            ]
        },
        {"type": "divider"}
    ])

    return answer_blocks