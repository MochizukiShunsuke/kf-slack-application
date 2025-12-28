import os
import base64
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

def analyze_receipt(image_content):
    base64_image = base64.b64encode(image_content).decode('utf-8')
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
                            "url": f"data:image/jpeg;base64,{base64_image}"
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