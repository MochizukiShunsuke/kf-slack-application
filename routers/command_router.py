from config import IS_PROD
from listeners.accounting_command_listener import handle_accounting_from_command
from listeners.rag_listener import handle_rag_from_command
from listeners.zoom_listener import handle_meeting_summary_from_command

<<<<<<< HEAD
def register_command_router(app):
    suffix = "" if IS_PROD else "-dev"

    app.command(f"/accounting{suffix}")(handle_accounting_from_command)
    app.command(f"/rag{suffix}")(handle_rag_from_command)
    app.command(f"/meeting-summary{suffix}")(handle_meeting_summary_from_command)
=======
def register_command_router(slack_app):
    suffix = "" if IS_PROD else "-dev"

    slack_app.command(f"/accounting{suffix}")(handle_accounting_from_command)
    slack_app.command(f"/rag{suffix}")(handle_rag_from_command)
    slack_app.command(f"/meeting-summary{suffix}")(handle_meeting_summary_from_command)
>>>>>>> 6146bfa (Release v1.5.0 : PC & overall reservation and Zoom function)
