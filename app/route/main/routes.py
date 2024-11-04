import uuid
from flask import render_template,make_response, request, send_from_directory

from app.models import Client
from app.extension import db
from . import main_bp
from flask import current_app

@main_bp.route("/", methods=["GET"])
def index():
    current_app.logger.info("main route called")
    response = make_response(render_template('index.html'))

    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # Take the first IP if there are multiple IPs listed
        client_ip = x_forwarded_for.split(',')[0]
    else:
        client_ip = request.remote_addr
    session = Client(client_session_id=str(uuid.uuid4()),ip=client_ip)
    db.session.add(session)
    db.session.commit()

    # Set the session ID in the response header
    response.set_cookie('Session-ID', session.client_session_id, httponly=True, max_age=60*60*24)  # expires in 1 day
    response.set_cookie('Session-SALT', session.salt, httponly=True, max_age=60*60*24)  # expires in 1 day

    return response

@main_bp.route('/login')
def loginPage():
    response = make_response(render_template('login.html'))

    session_ID = request.cookies.get('Session-ID')

    if session_ID is not None:
        session = Client.query.filter_by(client_session_id = session_ID).first()
        if session is not None:
            if session.isValid():
                response.set_cookie('Session-ID', session.client_session_id, httponly=True, max_age=60*60*24)  # expires in 1 day
                response.set_cookie('Session-SALT', session.salt, httponly=True, max_age=60*60*24)  # expires in 1 day
                return response

    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        # Take the first IP if there are multiple IPs listed
        client_ip = x_forwarded_for.split(',')[0]
    else:
        client_ip = request.remote_addr
    session = Client(client_session_id=str(uuid.uuid4()),ip=client_ip)
    db.session.add(session)
    db.session.commit()

    # Set the session ID in the response header
    response.set_cookie('Session-ID', session.client_session_id, httponly=True, max_age=60*60*24)  # expires in 1 day
    response.set_cookie('Session-SALT', session.salt, httponly=True, max_age=60*60*24)  # expires in 1 day
    return response
