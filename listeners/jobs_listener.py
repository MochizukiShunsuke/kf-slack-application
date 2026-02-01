import os
import logging
from flask import request, jsonify
from slack_sdk import WebClient

from features.activity_report_feature import run_activity_report_reminder, generate_activity_report

logger = logging.getLogger(__name__)

slack_client = WebClient(token=os.environ.get("SLACK_BOT_TOKEN"))

def handle_activity_report_job():
    try:
        data = request.get_json(silent=True) or {}
        job_type = data.get("type")

        if job_type == "generation":
            user_id = data.get("user_id")
            channel_id = data.get("channel_id")
            target_month = data.get("target_month")
            print(f"jobs_listener.py:{target_month}")
            
            logger.info(f"Starting generation job for {user_id}")

            generate_activity_report(slack_client, channel_id, user_id, target_month)
            
            return jsonify({"status": "success", "job": "generation"}), 200

        else:

            logger.info("Starting reminder job")
            result = run_activity_report_reminder()
            return jsonify({"status": "success", "job": "reminder", "detail": result}), 200

    except Exception as e:
        logger.exception("Handle Activity Report Job Error")
        return jsonify({"status": "error", "message": str(e)}), 500