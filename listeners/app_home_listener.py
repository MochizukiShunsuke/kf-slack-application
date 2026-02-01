import logging
from features.app_home_feature import render_app_home

logger = logging.getLogger(__name__)

def handle_app_home_opened(event, client, logger):
    try:
        user_id = event["user"]
        render_app_home(user_id)
    except Exception as e:
        logger.error(f"Error in handle_app_home_opened: {e}")