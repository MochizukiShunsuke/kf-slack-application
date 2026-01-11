import os
import base64
import io
import logging
import fitz
from PIL import Image
from openai import OpenAI

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_receipt(file_content, mimetype="image/jpeg"):
    print(f"---Analyze {mimetype} Start---")
    try:
        if mimetype == "application/pdf":
            try:
                doc = fitz.open(stream=file_content, filetype="pdf")
                page = doc.load_page(0)
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                file_content = pix.tobytes("jpeg")
                mimetype = "image/jpeg"
                doc.close()
                print("---Converted PDF to JPEG---")
            except Exception as e:
                logger.error(f"PDF conversion failed: {e}")
                return None
        
        supported_mimetypes = ["image/jpeg", "image/png", "image/webp", "image/gif"]
        if mimetype not in supported_mimetypes:
            try:
                img = Image.open(io.BytesIO(file_content))
                img = img.convert("RGB")
                buffer = io.BytesIO()
                img.save(buffer, format="JPEG")
                file_content = buffer.getvalue()
                mimetype = "image/jpeg"
                print("---Converted Image to JPEG---")
            except Exception as e:
                logger.warning(f"Image conversion failed: {e}")
        
        base64_data = base64.b64encode(file_content).decode('utf-8')
        
        prompt = """あなたはレシート画像を解析し、構造化データを返すAPIです。
    以下の情報を抽出して、以下のようにデータを成形してください。

    【重要：禁止事項】
    - Markdownのコードブロック記法は絶対に使用しないでください。

    【抽出項目】
    キー名は以下に固定してください。
    1. "日付": 購入日 (YYYY/MM/DD形式。年不明なら今年)
    2. "内容": 内容 (店舗名と代表商品名。例: "DCM (プラダン2枚，接着剤1本)")
    3. "内訳": 内訳 (金額計算式。例: "877円x2+1,408円")
    4. "金額": 合計金額 (半角数値のみ)

    【出力例】
    "日付": "2025/08/03",
    "内容": "DCM (プラダン、接着剤)",
    "内訳": "877円x2+1,408円",
    "金額": ¥3,162"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mimetype};base64,{base64_data}"
                            }
                        },
                    ],
                }
            ],
            max_tokens=500,
        )
        content = response.choices[0].message.content
        
        parsed_data = {}
        for line in content.split("\n"):
            line = line.replace('"', '').replace(',', '').strip()
            if ":" in line:
                k, v = line.split(":", 1)
                parsed_data[k.strip()] = v.strip()
                
        return parsed_data
    except Exception:
        logger.exception("Analyze Receipt Error")
        return None



def summarize_text(full_text):
    """
    長文の会議ログを、Slackで見やすい書式で要約する (gpt-4o-mini対応版)
    """
    MAX_CHUNK_LENGTH = 20000 
    
    # 1回で処理できる長さの場合
    if len(full_text) <= MAX_CHUNK_LENGTH:
        return call_openai_api(full_text, get_final_instruction())

    # --- 分割処理 (Mapステップ) ---
    chunks = [full_text[i:i + MAX_CHUNK_LENGTH] for i in range(0, len(full_text), MAX_CHUNK_LENGTH)]
    partial_summaries = []
    
    for i, chunk in enumerate(chunks):
        # 中間要約は情報を落としすぎないように指示
        summary = call_openai_api(chunk, "このセクションの議論内容と決定事項を箇条書きで整理してください。")
        partial_summaries.append(summary)

    # --- 統合・文脈調整ステップ (Reduceステップ) ---
    combined_summary = "\n\n--- 次のセクション ---\n\n".join(partial_summaries)
    return call_openai_api(combined_summary, get_final_instruction())

def get_final_instruction():
    """
    Slackで見やすくするための専用指示（プロンプト）
    """
    return (
        "以下の会議ログ（または分割要約）を、Slackで読みやすい形式に統合して要約してください。\n\n"
        "*【Slack専用の書式ルール】*\n"
        "1. 見出しに '#' は絶対に使わず、 *太字* で表現してください。\n"
        "2. 太字はアスタリスク1つで挟む *太字* にしてください（**太字** はNGです）。\n"
        "3. 箇条書きは '-' を使用し、適宜インデント（スペース2つ）を入れてください。\n"
        "4. 適宜、内容に合った『絵文字』を文頭に入れて視認性を高めてください。\n\n"
        "【構成案】\n"
        "📢 *会議の全体概要*\n"
        "（ここに1行で概要）\n\n"
        "📝 *主なトピックと議論内容*\n"
        "（ここにトピックごとの箇条書き）\n\n"
        "✅ *決定事項・ネクストアクション*\n"
        "（ここを最重要として3点に絞る）"
    )

def call_openai_api(text, instruction):
    """
    OpenAI APIを呼び出す共通関数
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # 高速・大容量・低価格
            messages=[
                {"role": "system", "content": "あなたは優秀な議事録作成アシスタントです。出力はすべてSlackのmrkdwn形式で行います。"},
                {"role": "user", "content": f"{instruction}\n\n{text}"}
            ],
            temperature=0.3
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI API Error: {e}")
        return f"要約エラーが発生しました: {e}"