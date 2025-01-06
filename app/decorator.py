#decorator
from functools import wraps
import json
from pprint import pprint

from flask import jsonify, request,current_app as app

from app.models import Client, UserRole
from app.util import decode_text
from app.mylogger import error_logger


def checkBlueprintRouteFlag(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if app.config.get('BLUEPRINT_ROUTE'):
			return f(*args, **kwargs)
		else:
			error_logger.info("Blueprint_route flag is disabled")
			return jsonify({"message":"route not found"}),404
	return decorated_function


def verify_internal_api_id(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		api_id = request.headers.get('API-ID')

		if api_id is None:
			error_logger.error(f'API Id not passed')
			return  jsonify({"message":"Not a valid API request"}),401
   

		if api_id != app.config.get('API_ID'):
			error_logger.error(f'session does not have valid API-ID : {api_id}')
			return jsonify({"message":"Not a valid API request."}),401

		return f(*args, **kwargs)
	return decorated_function


def verify_body(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		request_data = request.json
		
		if request_data is None:
			return jsonify({"message":"Invalid request data format"}),401
		
		session_id = request.cookies.get('Session-ID')
		session = Client.query.filter_by(client_session_id=session_id).first()
		data_str = decode_text(session.salt,request_data['data'].encode('UTF-8')).replace("\t", "\\t").replace("\n", "\\n").replace("\r", "\\r")

		data = json.loads(data_str)
		return f(data,*args, **kwargs)
	return decorated_function


def verify_session(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			error_logger.error(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			error_logger.error(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			error_logger.error(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401
		
		return f(session,*args, **kwargs)
	return decorated_function

def verify_user(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			error_logger.error(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			error_logger.error(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			error_logger.error(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			error_logger.error(f'User id not found in the db for a valid session: {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user:
			return f(session,*args, **kwargs)
		  
		error_logger.error(f'Something went wrong with request')
		return jsonify({"message":"Something went wrong."}),401
	return decorated_function


def verify_FACULTY_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			error_logger.error(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			error_logger.error(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			error_logger.error(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			error_logger.error(f'User id not found in the db for a valid session: {session_id}')
			return jsonify({"message":"User is not logged in"}),401


		if session.user.has_role(UserRole.FACULTY):
			return f(session,*args, **kwargs)
		else:
			error_logger.error(f'User is not authorised')
			return jsonify({"message":"Unauthorized User"}),401

	return decorated_function


def verify_SUPERADMIN_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			error_logger.error(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			error_logger.error(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			error_logger.error(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			error_logger.error(f'User id not found in the db for a valid session: {session_id}')
			return jsonify({"message":"User is not logged in"}),401


		if session.user.has_role(UserRole.SUPERADMIN):
			return f(session,*args, **kwargs)
		else:
			error_logger.error(f'User is not authorised')
			return jsonify({"message":"Unauthorized User"}),401

	return decorated_function

def verify_LIBRARYMANAGER_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			error_logger.error(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			error_logger.error(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			error_logger.error(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			error_logger.error(f'User id not found in the db for a valid session: {session_id}')
			return jsonify({"message":"User is not logged in"}),401


		if session.user.has_role(UserRole.LIBRARYMANAGER):
			return f(session,*args, **kwargs)
		else:
			error_logger.error(f'User is not authorised')
			return jsonify({"message":"Unauthorized User"}),401

	return decorated_function


def verify_GUEST_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			error_logger.error(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			error_logger.error(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			error_logger.error(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		return f(session,*args, **kwargs)
	return decorated_function

def verify_USER_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			error_logger.error(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			error_logger.error(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			error_logger.error(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			error_logger.error(f'User id not found in the db for a valid session: {session_id}')
			return jsonify({"message":"Not a valid Session."}),401


		if session.user.has_role(UserRole.FACULTY) or session.user.has_role(UserRole.RESIDENT):
			return f(session,*args, **kwargs)
		else:
			pprint(session.user)
			error_logger.error(f'User is not authorised')
			return jsonify({"message":"Unauthorized User"}),401

	return decorated_function

