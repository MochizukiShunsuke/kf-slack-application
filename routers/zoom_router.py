from flask import request
from listeners.zoom_listener import handle_ingest

<<<<<<< HEAD
def register_zoom_router(flask_app, db):
    @flask_app.route("/ingest", methods=["POST"])
    def ingest_route():
        return handle_ingest(request, db)
=======
def register_zoom_router(flask_app):
    @flask_app.route("/ingest", methods=["POST"])
    def ingest_route():
        return handle_ingest(request)
>>>>>>> 6146bfa (Release v1.5.0 : PC & overall reservation and Zoom function)
