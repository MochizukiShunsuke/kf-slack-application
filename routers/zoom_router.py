from flask import request
from listeners.zoom_listener import handle_ingest

def register_zoom_router(flask_app, db):
    @flask_app.route("/ingest", methods=["POST"])
    def ingest_route():
        return handle_ingest(request, db)