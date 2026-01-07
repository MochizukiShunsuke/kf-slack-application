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