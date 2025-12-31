from listeners.accounting_listener import handle_accounting_from_command
from listeners.rag_listener import handle_rag_from_command

def register_command_router(app):
    app.command("/accounting")(handle_accounting_from_command)
    app.command("/rag")(handle_rag_from_command)