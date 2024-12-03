
from datetime import timedelta
import json
import os
from flask import current_app as app, jsonify, request, send_file
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

configs = [
		'OTP_FLAG',
		'OTP_GENERATION',
		'LOG_REQUEST',
		'LOG_RESPONSE',
		'OTP_DELTA',
		'OTP_MAX_ATTEMPT',
		'SALT_PASSWORD',
		'COOKIE_AGE',
		'API_ID',
		'BLUEPRINT_ROUTE',
  
		'MAIL_SERVER',
		'MAIL_PORT',
		'MAIL_USERNAME',
		'MAIL_PASSWORD',
		'MAIL_USE_TLS',
		'MAIL_USE_SSL',

		'OTP_SERVER',
		'OTP_USERNAME',
		'OTP_PASSWORD',
		'OTP_ID',
		'OTP_SENDERID',

		'UPLOAD_FOLDER',
	]
	


def serialize_timedelta(obj):
	if isinstance(obj, timedelta):
		return str(obj)  # Serialize timedelta as a string
	return obj


def string_to_timedelta(time_str):
    # Example: "1:30:15" (1 hour, 30 minutes, 15 seconds)
    hours, minutes, seconds = map(int, time_str.split(":"))
    return timedelta(hours=hours, minutes=minutes, seconds=seconds)



@superadmin_bp.route("/export/config")
@verify_SUPERADMIN_role
def export_config(session):
	data = {}
	
	for config in configs:
		data[config] = app.config[config]
	
	file_path = os.path.join(os.getcwd(), "uploads", "export", "data.json")

	# Write JSON object to a file
	with open(file_path, 'w') as json_file:
		json.dump(data, json_file, indent=4,default=serialize_timedelta)

	return send_file(file_path,as_attachment=True,mimetype='application/json',
				download_name='data.json'),200


@superadmin_bp.route("/import/config",methods=['POST'])
@verify_SUPERADMIN_role
def import_config(session):
	if 'file' not in request.files:
		return jsonify({"error": "No file part in the request"}), 400

	file = request.files['file']
	file_path = os.path.join(os.getcwd(), "uploads", "export", "data.json")

	# Check if a file was submitted
	if file.filename == '':
		return jsonify({"error": "No file selected"}), 400

	# Check if the file is allowed
	if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ['json']:
		file.save(file_path)
		with open(file_path, 'r') as json_file:
			imported_data = json.load(json_file)
			for config in configs:
				if config == 'OTP_DELTA':
					app.config[config] = string_to_timedelta(imported_data[config])
				else:
					app.config[config] = imported_data[config]
				app.logger.info(f"Setting config [{config}] = {imported_data[config]}")
		return jsonify({"message":"successfull upload of the data"}),200

	return jsonify({"error": "Invalid file type. Only .json files are allowed."}), 401


@superadmin_bp.route("/export/dbFetch")
@verify_SUPERADMIN_role
def export_dbFetch(session):
	return send_file("app.db",as_attachment=True)

