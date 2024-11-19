
from flask import current_app as app
from app.decorator import checkBlueprintRouteFlag, verify_SUPERADMIN_role
from . import public_bp

@public_bp.route("/")
@checkBlueprintRouteFlag
@verify_SUPERADMIN_role
def index(session):
	return "This is research repository public route"
