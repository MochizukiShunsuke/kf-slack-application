import os

RAG_CHANNEL_ID = os.environ.get("RAG_CHANNEL_ID")
ACCOUNTING_CHANNEL_ID = os.environ.get("ACCOUNTING_CHANNEL_ID")
ACTIVITY_REPORT_CHANNEL_ID = os.environ.get("ACTIVITY_REPORT_CHANNEL_ID")

ALLOWED_MENTION_CHANNELS = [
    RAG_CHANNEL_ID
]

accounting_users_str = os.environ.get("ACCOUNTING_USERS", "")
if accounting_users_str:
    ACCOUNTING_USERS = set(accounting_users_str.split(","))
else:
    ACCOUNTING_USERS = set()