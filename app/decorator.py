#decorator
from functools import wraps
import json

from flask import jsonify, request,current_app as app

from app.models import Client, UserRole
from app.util import decode_text

def verify_body(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		request_data = request.json
		
		if request_data is None:
			return jsonify({"message":"Invalid request data format"}),401
		
		session_id = request.cookies.get('Session-ID')
		session = Client.query.filter_by(client_session_id=session_id).first()
		app.logger.info(request_data)
		data_str = decode_text(session.salt,request_data['data'].encode('UTF-8'))
		app.logger.info(data_str)
		data = json.loads(data_str)
		app.logger.info(data)
		return f(data,*args, **kwargs)
	return decorated_function


def verify_session(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			app.logger.info(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			app.logger.info(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			app.logger.info(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401
		
		return f(session,*args, **kwargs)
	return decorated_function

def verify_user(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			app.logger.info(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			app.logger.info(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			app.logger.info(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			app.logger.info(f'User id not found in the db for a valid session: {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user:
			return f(session,*args, **kwargs)
		  
		app.logger.info(f'Something went wrong with request')
		return jsonify({"message":"Something went wrong."}),401
	return decorated_function

def verify_SUPERADMIN_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			app.logger.info(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			app.logger.info(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			app.logger.info(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			app.logger.info(f'User id not found in the db for a valid session: {session_id}')
			return jsonify({"message":"Not a valid Session."}),401


		if session.user.has_role(UserRole.SUPERADMIN):
			return f(session,*args, **kwargs)
		else:
			return jsonify({"message":"Unauthorized User"}),401

	return decorated_function


def verify_GUEST_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.cookies.get('Session-ID')

		if session_id is None:
			app.logger.info(f'Session Id not passed')
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			app.logger.info(f'session does not exsit in the db : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			app.logger.info(f'session is not valid : {session_id}')
			return jsonify({"message":"Not a valid Session."}),401

		return f(session,*args, **kwargs)
	return decorated_function



