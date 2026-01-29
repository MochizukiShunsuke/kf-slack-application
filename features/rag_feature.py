import logging
from services.openai_service import create_embedding, create_chat_completion
from services.pinecone_service import query_pinecone

logger = logging.getLogger(__name__)

def get_rag_response_blocks(query_text, chat_history=None):
    try:
        query_vector = create_embedding(query_text)
        search_results = query_pinecone(query_vector)
        matches = search_results.get('matches', [])
        
        if not matches:
            return [{"type": "section", "text": {"type": "mrkdwn", "text": "⚠️ 提供されたデータ内に情報が見つかりませんでした。"}}]
        
        formatted_contexts = []
        for m in matches:
            rid = m['metadata'].get('rule_id', 'Unknown ID')
            en_text = m['metadata'].get('English_Text', '')
            jp_text = m['metadata'].get('Japanese_Text', '')
            context_block = f"--- [Rule ID: {rid}] (Score: {m.get('score', 0):.4f}) ---\nEnglish: {en_text}\nJapanese: {jp_text}"
            formatted_contexts.append(context_block)
        
        combined_context = "\n\n".join(formatted_contexts)
        
        system_prompt = """あなたは学生フォーミュラ（Formula Student）の車両製作レギュレーション(FSAE-Rules)の検索アシスタントです。
    検索結果（コンテキスト）に記載された関連度スコア(Score)に基づき、上位5件を特定して回答してください。

    回答のルール
    1. 根拠の明示: 回答の際は、必ず参照した「rule_id」を文中に明記してください。
    2. スコアの扱い: 検索結果に含まれる「Score」は Pinecone による近似度を示します。これを「関連度スコア」として出力に使用してください。
    3. 太字（**text**）や箇条書き（* item）などの装飾にアスタリスクを使わないでください。なお装飾以外の場合では認めます。
    4. 参照ソース欄では、必ず metadata の Japanese_Text をそのまま引用してください。English_Text を翻訳・要約・引用してはいけません。

    出力フォーマット
    回答は以下の構成で出力してください：

    【回答】
    （原文を根拠とした詳しい解説）

    【参照ソース（関連度スコア順 Top 5）】
    （ここにスコアの高い順に5件リストアップしてください。形式は厳守）
    -【rule_id】
    (Japanese_Text) / 関連度: スコア
    -【rule_id】
    (Japanese_Text) / 関連度: スコア
    ...
    """
        
        messages = [{"role": "system", "content": system_prompt}]
        
        if chat_history:
            messages.extend(chat_history)
        
        messages.append({
            "role": "user", 
            "content": f"## コンテキスト:\n{combined_context}\n\n## 質問:\n{query_text}"
        })
        
        raw_answer = create_chat_completion(messages)
        
        return _build_slack_blocks(query_text, raw_answer)

    except Exception:
        logger.exception("RAG Feature Error")
        return [{"type": "section", "text": {"type": "mrkdwn", "text": "⚠️ 回答の生成中にエラーが発生しました。"}}]

def _build_slack_blocks(query_text, response_text):
    delimiter = "【参照ソース（関連度スコア順 Top 5）】"
    if delimiter in response_text:
        idx = response_text.find(delimiter)
        main_answer = response_text[:idx].strip()
        reference_part = response_text[idx:].strip()
    else:
        main_answer = response_text.strip()
        reference_part = ""
    
    quoted_question = "\n".join([f">{line}" for line in query_text.strip().splitlines()])
    
    answer_blocks = [
        {"type": "divider"},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*❓ 質問内容*\n{quoted_question}"}},
        {"type": "section", "text": {"type": "mrkdwn", "text": f"*💡 AIの回答*\n\n{main_answer}"}}
    ]

    if reference_part:
        answer_blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"```\n{reference_part}\n```"}
        })

    answer_blocks.extend([
        {"type": "context", "elements": [{"type": "mrkdwn", "text": "⚠️ *注意:* 最終的な判断は参照元:FSAE Rules 2026を確認してください。"}]},
        {"type": "divider"}
    ])
    return answer_blocks