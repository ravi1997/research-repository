from flask import send_from_directory
from . import main_bp
from flask import current_app

@main_bp.route("/", methods=["GET"])
def index():
    current_app.logger.info("main route called")
    return send_from_directory(current_app.static_folder, 'index.html')


""" @main_bp.route('/<path:path>')
def serve_static(path):
    current_app.logger.info("main route static server called")
    return send_from_directory(current_app.static_folder, path) """