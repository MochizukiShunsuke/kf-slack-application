import os

# ===== Environment =====
ENV = os.environ.get("ENV")
if ENV not in ("production", "development"):
    raise RuntimeError(f"ENV is not set correctly: {ENV}")

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