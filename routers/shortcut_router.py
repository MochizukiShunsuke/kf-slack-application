from listeners.accounting_shortcut_listener import handle_receipt_shortcut

def register_shortcut_router(slack_app):
    slack_app.shortcut("open_receipt_modal_shortcut")(handle_receipt_shortcut)