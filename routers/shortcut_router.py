from listeners.accounting_shortcut_listener import handle_receipt_shortcut

<<<<<<< HEAD
def register_shortcut_router(app):
    app.shortcut("open_receipt_modal_shortcut")(handle_receipt_shortcut)
=======
def register_shortcut_router(slack_app):
    slack_app.shortcut("open_receipt_modal_shortcut")(handle_receipt_shortcut)
>>>>>>> 6146bfa (Release v1.5.0 : PC & overall reservation and Zoom function)
