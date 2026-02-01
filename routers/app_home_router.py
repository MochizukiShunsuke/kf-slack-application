from listeners.app_home_listener import handle_app_home_opened

def register_app_home_router(slack_app):
    slack_app.event("app_home_opened")(handle_app_home_opened)