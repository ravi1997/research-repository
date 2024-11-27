from flask import jsonify,current_app

from app.decorator import checkBlueprintRouteFlag, verify_SUPERADMIN_role, verify_body, verify_user
from app.models import User
from app.extension import db

from app.models.user import UserRole, UserRoles
from app.schema import UserSchema
from . import user_bp

@user_bp.route("/")
@checkBlueprintRouteFlag
@verify_SUPERADMIN_role
def index(session):
    return "This is research repository user route"

@user_bp.route("/getAll", methods=["GET"])
@verify_SUPERADMIN_role
def getAll_users(session):
    schemas = UserSchema(many=True)
    users = User.query.all()
    return schemas.jsonify(users), 200


@user_bp.route("/create",methods=["POST"])
@verify_user
@verify_body
def createUser(data,session):
    userSchema = UserSchema()
    if session.user.has_role(UserRole.SUPERADMIN):
        user = userSchema.loads(data)
        user.roles.append(UserRoles(role=UserRole.LIBRARYMANAGER))
        return jsonify({"message":"User created successfully"}),200
    
    if session.user.has_role(UserRole.LIBRARYMANAGER):
        user = userSchema.loads(data)
        user.roles.append(UserRoles(role=UserRole.FACULTY),UserRoles(role=UserRole.RESIDENT))
        return jsonify({"message":"User created successfully"}),200
    
    return jsonify({"message":"Unauthorized User"}),401