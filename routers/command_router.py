from config import IS_PROD
from listeners.accounting_command_listener import handle_accounting_from_command
from listeners.rag_listener import handle_rag_from_command
from listeners.zoom_listener import handle_meeting_summary_from_command
from listeners.activity_report_listener import handle_activity_report_from_command
from listeners.timecard_listener import handle_timecard_command

def register_command_router(slack_app):
    suffix = "" if IS_PROD else "-dev"

    slack_app.command(f"/accounting{suffix}")(handle_accounting_from_command)
    slack_app.command(f"/rag{suffix}")(handle_rag_from_command)
    slack_app.command(f"/meeting-summary{suffix}")(handle_meeting_summary_from_command)
    slack_app.command(f"/activity-report{suffix}")(handle_activity_report_from_command)
    slack_app.command(f"/timecard{suffix}")(handle_timecard_command)