
from flask import current_app as app, jsonify, send_file
from app.decorator import checkBlueprintRouteFlag, verify_SUPERADMIN_role, verify_body
from . import superadmin_bp

@superadmin_bp.route("/")
@checkBlueprintRouteFlag
@verify_SUPERADMIN_role
def index(session):
	return "This is research repository superadmin route"


@superadmin_bp.route("/config/otp-flag")
@verify_SUPERADMIN_role
def otp_flag_get(session):
	return jsonify({"value":app.config['OTP_FLAG']}),200

@superadmin_bp.route("/config/otp-flag",methods=["POST"])
@verify_SUPERADMIN_role
@verify_body
def otp_flag_set(data,session):
	app.config['OTP_FLAG'] = data['value']
	return jsonify({"message":"value is updated"}),200

@superadmin_bp.route("/config/otp-generation")
@verify_SUPERADMIN_role
def otp_generation_get(session):
	return jsonify({"value":app.config['OTP_GENERATION']}),200

@superadmin_bp.route("/config/otp-generation",methods=["POST"])
@verify_SUPERADMIN_role
@verify_body
def otp_generation_set(data,session):
	app.config['OTP_GENERATION'] = data['value']
	return jsonify({"message":"value is updated"}),200





@superadmin_bp.route("/dbFetch")
@verify_SUPERADMIN_role
def dbFetch(session):
	return  send_file("app.db",as_attachment=True)

