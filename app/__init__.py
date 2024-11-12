from logging.handlers import RotatingFileHandler
from sqlalchemy import Text

import json
import logging
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from app.config import DevConfig
from app.mylogger import *
from .extension import db, migrate,ma,bcrypt,scheduler
from .route.main import main_bp
from .route.auth import auth_bp
from .route.public import public_bp
from .route.user import user_bp
from app.extra import job_listener
from apscheduler.events import EVENT_JOB_EXECUTED
from app.db_initializer import seed_db_command, empty_db_command,test_command
from app.models import *

def create_app():
	app = Flask(__name__,static_folder='static')
	app.config.from_object(DevConfig)

	# Initialize extensions
	db.init_app(app)
	migrate.init_app(app, db)
	ma.init_app(app)
	bcrypt.init_app(app)
	scheduler.init_app(app)
	scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED)
	CORS(app)
	scheduler.start()


	os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
	filedir = os.path.join(app.config["UPLOAD_FOLDER"],'pubfetch')
	os.makedirs(filedir, exist_ok=True)

	app.cli.add_command(seed_db_command)
	app.cli.add_command(test_command)
	app.cli.add_command(empty_db_command)

	# Define the log directory
	log_dir = os.path.join('logs')
	os.makedirs(log_dir, exist_ok=True)

	# Define log files
	app_log_file = os.path.join(log_dir, 'app.log')
	error_log_file = os.path.join(log_dir, 'error.log')
	request_log_file = os.path.join(log_dir, 'request.log')

	# Create a formatter with a custom format
	formatter = logging.Formatter(
		"%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
	)

	# Create handlers for each log
	# 1. Application Log
	app_handler = RotatingFileHandler(
		app_log_file,
		maxBytes=10 * 1024 * 1024,  # Max log file size: 10 MB
		backupCount=5  # Keep 5 backup logs
	)
	app_handler.setFormatter(formatter)

	# 2. Error Log
	error_handler = RotatingFileHandler(
		error_log_file,
		maxBytes=10 * 1024 * 1024,  # Max log file size: 10 MB
		backupCount=5  # Keep 5 backup logs
	)
	error_handler.setFormatter(formatter)

	# 3. Request Log
	request_handler = RotatingFileHandler(
		request_log_file,
		maxBytes=10 * 1024 * 1024,  # Max log file size: 10 MB
		backupCount=5  # Keep 5 backup logs
	)
	request_handler.setFormatter(formatter)

	# Add the handlers to specific loggers
	# Application Logger
	app.logger.addHandler(app_handler)
	app.logger.setLevel(logging.INFO)

	# Error Logger
	error_logger.addHandler(error_handler)
	error_logger.setLevel(logging.ERROR)

	# Request Logger

	request_logger.addHandler(request_handler)
	request_logger.setLevel(logging.INFO)


	app.logger.propagate = False
	app.logger.info("Flask app startup")


	@app.errorhandler(404)
	def page_not_found(e):
		# Get the URL that caused the error
		url = request.url
		method = request.method
		error_logger.error(f"main app route : {url} {method} not found 404")
		return jsonify({"message":f"Url not found : {url} {method}"}),404
		


	@app.before_request
	def log_request():
		if app.config['LOG_REQUEST']:
			log  = "\n=== New Request ===\n"
			log += f"Request Method: {request.method}\n"
			log += f"Request URL: {request.url}\n"
			
			headers = dict(request.headers)
			log += f"Headers: {json.dumps(headers, indent=2)}\n"
			log += f"Query Parameters: {request.args.to_dict()}\n"

			# Log form data (for POST or PUT requests)
			if request.form:
				log += f"Form Data: {request.form.to_dict()}\n"
			
			# Log JSON body if present
			if request.is_json:
				log += f"JSON Body: {request.get_json()}\n"
			else:
				# Log raw body as text if it's not JSON
				log += f"Body (raw text): {request.get_data(as_text=True)}\n"
			
			# Log cookies
			log += f"Cookies: {request.cookies.to_dict()}\n"
			
			# Log client information
			real_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
			log += f"Client IP: {real_ip}\n"
			log += f"Client User Agent: {request.user_agent}\n"
			
			log += "=== End of Request Log ==="

			request_logger.info(log)
		

	# Register blueprints
	app.register_blueprint(main_bp, url_prefix="/researchrepository")
	app.register_blueprint(auth_bp, url_prefix="/researchrepository/api/auth")
	app.register_blueprint(public_bp, url_prefix="/researchrepository/api/public")
	app.register_blueprint(user_bp, url_prefix="/researchrepository/api/user")
	return app
