import os

# ===== Environment =====
ENV = os.environ.get("ENV")
# ローカル開発などでENV未設定の場合のフォールバックが必要なら修正してください
# if ENV not in ("production", "development"):
#     raise RuntimeError(f"ENV is not set correctly: {ENV}")

IS_PROD = ENV == "production"

# ===== Channel IDs =====
RAG_CHANNEL_ID = os.environ.get("RAG_CHANNEL_ID")
ACCOUNTING_CHANNEL_ID = os.environ.get("ACCOUNTING_CHANNEL_ID")
PC_RESERVATION_CHANNELS = ["C02CXQBJY31", "C0A5CNX9K7E"]
ACTIVITY_REPORT_CHANNEL_ID = os.environ.get("ACTIVITY_REPORT_CHANNEL_ID")
ALLOWED_MENTION_CHANNELS = [
    RAG_CHANNEL_ID
]

# ===== Accounting Users =====
accounting_users_str = os.environ.get("ACCOUNTING_USERS", "")
if accounting_users_str:
    ACCOUNTING_USERS = set(accounting_users_str.split(","))
else:
    ACCOUNTING_USERS = set()

# ===== Google Drive / Sheets IDs =====
ACCOUNTING_SHEET_ID = os.environ.get("ACCOUNTING_SHEET_ID")
ACTIVITY_REPORT_SHEET_ID = os.environ.get("ACTIVITY_REPORT_SHEET_ID")
MEMBER_MANAGER_SHEET_ID = os.environ.get("MEMBER_MANAGER_SHEET_ID")
ACTIVITY_REPORT_TEMPLATE_ID = os.environ.get("ACTIVITY_REPORT_TEMPLATE_ID")
MEMBER_PICTURE_FOLDER_ID = os.environ.get("MEMBER_PICTURE_FOLDER_ID")
ACTIVITY_PICTURE_FOLDER_ID = os.environ.get("ACTIVITY_PICTURE_FOLDER_ID")
ACTIVITY_REPORT_MESSAGE_FOLDER_ID = os.environ.get("ACTIVITY_REPORT_MESSAGE_FOLDER_ID")

SERVICE_URL = os.environ.get("SERVICE_URL")

# ===== Cloud Tasks Config =====
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT") 
REGION = os.environ.get("REGION") 
ACTIVITY_REPORT_QUEUE_NAME = os.environ.get("ACTIVITY_REPORT_QUEUE_NAME") 
SERVICE_ACCOUNT_EMAIL = os.environ.get("SERVICE_ACCOUNT_EMAIL")