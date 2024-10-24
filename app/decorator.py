#decorator
from functools import wraps

from flask import jsonify, request

from app.models import Client, UserRole

def verify_body(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		request_data = request.json
		
		if request_data is None:
			return jsonify({"message":"Invalid request data format"}),400
		
		return f(request_data,*args, **kwargs)
	return decorated_function


def verify_session(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.headers.get('Session-ID')

		if session_id is None:
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			return jsonify({"message":"Not a valid Session."}),401
		
		return f(session,*args, **kwargs)
	return decorated_function

def verify_user(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.headers.get('Session-ID')

		if session_id is None:
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			return jsonify({"message":"Not a valid user."}),401

		if session.user:
			return f(session,*args, **kwargs)
		return jsonify({"message":"Something went wrong."}),400
	return decorated_function

def verify_SUPERADMIN_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.headers.get('Session-ID')

		if session_id is None:
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			return jsonify({"message":"Not a valid user."}),401

		if session.user.has_role(UserRole.SUPERADMIN):
			return f(session,*args, **kwargs)
		else:
			return jsonify({"message":"Unauthorized User."}),401

	return decorated_function


def verify_GUEST_role(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		session_id = request.headers.get('Session-ID')

		if session_id is None:
			return  jsonify({"message":"Not a valid Session"}),401
   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is None:
			return jsonify({"message":"Not a valid Session."}),401

		if not session.isValid():
			return jsonify({"message":"Not a valid Session."}),401

		if session.user_id is None:
			return jsonify({"message":"Not a valid user."}),401

		if session.user.has_role(UserRole.GUEST):
			return f(session,*args, **kwargs)
		else:
			return jsonify({"message":"Unauthorized User."}),401

	return decorated_function



