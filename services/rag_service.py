import os
import json
from pinecone import Pinecone
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index(os.environ.get("PINECONE_INDEX_NAME"))

def run_rag_flow(query_text, chat_history=None):
    try:
        query_vector = openai_client.embeddings.create(
            input=query_text,
            model="text-embedding-3-small"
        ).data[0].embedding

        search_results = index.query(
            vector=query_vector,
            top_k=10,
            include_metadata=True
        )

        print("--- [DEBUG] Pinecone Search Results ---")
        print(json.dumps(search_results, indent=2, ensure_ascii=False, default=str))
        print("---------------------------------------")

        matches = search_results['matches']
        
        if not matches:
            return "提供されたレギュレーションデータ内には、その情報が見つかりませんでした。"

        formatted_contexts = []
        for m in matches:
            score = m.get('score', 0.0)
            rid = m['metadata'].get('rule_id', 'Unknown ID')
            en_text = m['metadata'].get('English_Text', '')
            jp_text = m['metadata'].get('Japanese_Text', '')

            context_block = f"--- [Rule ID: {rid}] (Score: {score:.4f}) ---\nEnglish: {en_text}\nJapanese: {jp_text}"
            formatted_contexts.append(context_block)
        
        combined_context = "\n\n".join(formatted_contexts)

        system_prompt = """あなたは学生フォーミュラ（Formula Student）の車両製作レギュレーション(FSAE-Rules)の検索アシスタントです。
    検索結果（コンテキスト）に記載された関連度スコア(Score)に基づき、上位5件を特定して回答してください。

    回答のルール
    1. 根拠の明示: 回答の際は、必ず参照した「rule_id」を文中に明記してください。
    2. スコアの扱い: 検索結果に含まれる「Score」は Pinecone による近似度を示します。これを「関連度スコア」として出力に使用してください。
    3. 太字（**text**）や箇条書き（* item）などの装飾にアスタリスクを使わないでください。なお装飾以外の場合では認めます。

    出力フォーマット
    回答は以下の構成で出力してください：

    【回答】
    （原文を根拠とした詳しい解説）

    【参照ソース（関連度スコア順 Top 5）】
    （ここにスコアの高い順に5件リストアップしてください。形式は厳守）
    -【rule_id】
    (japanese_text) / 関連度: スコア
    -【rule_id】
    (japanese_text) / 関連度: スコア
    ...
    """

        messages = [{"role": "system", "content": system_prompt}]

        if chat_history:
            messages.extend(chat_history)

        messages.append({
            "role": "user", 
            "content": f"## コンテキスト（スコア付き）:\n{combined_context}\n\n## 質問:\n{query_text}"
        })

        response = openai_client.chat.completions.create(
            model="gpt-4o", 
            messages=messages,
            temperature=0
        )
        
        return response.choices[0].message.content
    except Exception:
        logger.exception("Run Rag Flow Error")
        return None