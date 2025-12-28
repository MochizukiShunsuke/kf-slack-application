import os
from pinecone import Pinecone
from openai import OpenAI

openai_client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))
index = pc.Index(os.environ.get("PINECONE_INDEX_NAME"))

def run_rag_flow(query_text):
    # 1. ベクトル化
    query_vector = openai_client.embeddings.create(
        input=query_text,
        model="text-embedding-3-small"
    ).data[0].embedding
    
    # 2. Pinecone検索
    search_results = index.query(
        vector=query_vector,
        top_k=20,
        include_metadata=True
    )
    matches = search_results['matches']
    
    if not matches:
        return "提供されたレギュレーションデータ内には、その情報が見つかりませんでした。"

    contexts = [m['metadata'].get('text', '') for m in matches]
    combined_context = "\n\n".join(contexts)

    # 3. 回答生成 
    system_prompt = """あなたは学生フォーミュラ（Formula Student）の技術レギュレーションに精通した、厳格かつ親切なテクニカルアドバイザーです。
ユーザー（学生エンジニア）の質問に対し、提供された「FSAE-Rules」ツール（コンテキスト）のみを用いて回答してください。

## 重要：思考と回答のプロセス
1. **ツールの使用**: 提供された情報を使って必ず検索してください。
2. **原文の確認**: **判断の根拠は必ず「英語原文 (English_Text)」を優先**してください。
3. **根拠の明示**: 回答の際は、必ず参照したルールの **ID（例: T.1.1.2）** を文中に明記してください。

## 回答のルール
* **事実のみを伝える**: あなた自身の知識や推測は一切含めないでください。
* **「該当なし」の対応**: 関連情報がない場合は「提供されたレギュレーションデータ内には、その情報が見つかりませんでした。」と伝えてください。
* **言語**: 回答はすべて **日本語** で行ってください。専門用語には英語原文を添えることが推奨されます。

## 出力フォーマット
**【結論】**
（簡潔な答え）

**【詳細・根拠】**
* **[ルールID]**:（内容を要約）

**【補足】**
（注意点などがあれば）"""
    response = openai_client.chat.completions.create(
        model="gpt-4o", 
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"--- コンテキスト ---\n{combined_context}\n\n--- 質問 ---\n{query_text}"}
        ],
        temperature=0
    )
    
    return response.choices[0].message.content