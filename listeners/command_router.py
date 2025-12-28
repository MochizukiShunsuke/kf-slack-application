from listeners.accounting import handle_accounting_from_command

def register_command_router(app):
    app.command("/accounting")(handle_accounting_from_command)