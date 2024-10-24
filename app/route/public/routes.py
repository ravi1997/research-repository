from flask import jsonify,current_app
from . import public_bp


@public_bp.route("/")
def index():
    return "This is The waiting list public route"
