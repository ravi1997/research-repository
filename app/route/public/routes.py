
from datetime import datetime
import uuid
from flask import current_app, jsonify, request
from app.decorator import checkBlueprintRouteFlag, verify_SUPERADMIN_role, verify_internal_api_id
from app.models.user import Client, ValidState
from app.utility import getIP
from . import public_bp
from app.extension import db,scheduler

@public_bp.route("/")
@checkBlueprintRouteFlag
@verify_SUPERADMIN_role
def index(session):
	return "This is research repository public route"


def invalid_SESSION(id):
    with current_app.app_context():
        client = Client.query.filter_by(id=id).first()
        if client:
            client.status = ValidState.INVALID
            db.session.commit()
            current_app.logger.info(f"Client {id} invalid successfully.")
        else:
            current_app.logger.error(f"Client with ID {id} not found for invalid.")


@public_bp.route("/generateSession")
@verify_internal_api_id
def generateSession():
    client_ip = getIP(request)
    client = request.args.get('ip', client_ip, type=str)
    
    current_app.logger.info(f"client IP : {client}")
    current_app.logger.info(f"client IP : {client_ip}")


    session = Client(client_session_id=str(uuid.uuid4()),ip=client)
    db.session.add(session)
    db.session.commit()
    
    scheduler.add_job(
      str(uuid.uuid4()),
      invalid_SESSION,
      trigger="date",
      run_date=datetime.now() + current_app.config['CLIENT_DELTA'],
      args=[session.id],
    )

    return jsonify({
		"Session-ID":session.client_session_id,
		"Session-SALT":session.salt
	}),200

