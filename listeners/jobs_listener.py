from flask import jsonify
from features.activity_report_feature import run_activity_report_reminder
import logging

logger = logging.getLogger(__name__)

def handle_activity_report_job():
    try:
        result = run_activity_report_reminder()
        return jsonify({"status": "success", "detail": result}), 200
    except Exception as e:
        logger.exception("Handle Activity Report Job Error")
        return jsonify({"status": "error", "message": str(e)}), 500