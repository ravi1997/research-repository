from flask import jsonify,current_app

from app.decorator import verify_SUPERADMIN_role
from app.models import User
from app.extension import db

from app.schema import UserSchema
from . import user_bp

@user_bp.route("/")
def index():
    return "This is The waiting list user route"

@user_bp.route("/getAll", methods=["GET"])
@verify_SUPERADMIN_role
def getAll_users(session):
    schemas = UserSchema(many=True)
    users = User.query.all()
    return schemas.jsonify(users), 200
