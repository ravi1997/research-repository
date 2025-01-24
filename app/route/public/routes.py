
import uuid
from flask import current_app as app, jsonify, request
from app.decorator import checkBlueprintRouteFlag, verify_SUPERADMIN_role, verify_internal_api_id
from app.models.user import Client
from app.utility import getIP
from . import public_bp
from app.extension import db

@public_bp.route("/")
@checkBlueprintRouteFlag
@verify_SUPERADMIN_role
def index(session):
	return "This is research repository public route"


@public_bp.route("/generateSession")
@verify_internal_api_id
def generateSession():
    client_ip = getIP(request)
    client = request.args.get('ip', client_ip, type=str)
    
    session = Client(client_session_id=str(uuid.uuid4()),ip=client)
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
		"Session-ID":session.client_session_id,
		"Session-SALT":session.salt
	}),200

