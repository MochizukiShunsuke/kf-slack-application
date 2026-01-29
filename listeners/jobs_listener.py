import os
import logging
from flask import request, jsonify
from slack_sdk import WebClient

# 機能をインポート
from features.activity_report_feature import run_activity_report_reminder, generate_activity_report

logger = logging.getLogger(__name__)

# Boltの外でSlack APIを叩くためのクライアント
slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def handle_activity_report_job():
    """
    Cloud Scheduler(催促) や Cloud Tasks(生成) から呼ばれるエンドポイント
    """
    try:
        # JSONデータを取得してみる
        data = request.get_json(silent=True) or {}
        job_type = data.get("type")

        # -------------------------------------------
        # ケース1: 報告書作成ジョブ (Cloud Tasksから)
        # -------------------------------------------
        if job_type == "generation":
            user_id = data.get("user_id")
            channel_id = data.get("channel_id")
            target_month = data.get("target_month")
            print(f"jobs_listener.py:{target_month}")
            
            logger.info(f"Starting generation job for {user_id}")
            
            # Featureの関数を実行 (slack_clientを渡す)
            generate_activity_report(slack_client, channel_id, user_id, target_month)
            
            return jsonify({"status": "success", "job": "generation"}), 200

        # -------------------------------------------
        # ケース2: 催促ジョブ (Cloud Scheduler等から)
        # -------------------------------------------
        else:
            # 既存のロジック (引数なし、またはtype指定なしの場合)
            logger.info("Starting reminder job")
            result = run_activity_report_reminder()
            return jsonify({"status": "success", "job": "reminder", "detail": result}), 200

    except Exception as e:
        logger.exception("Handle Activity Report Job Error")
        return jsonify({"status": "error", "message": str(e)}), 500