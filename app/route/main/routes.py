from datetime import datetime
import uuid
from flask import jsonify, render_template,make_response, request, send_from_directory
import requests

from app.decorator import verify_session, verify_user
from app.models import Client
from app.extension import db
from app.models.article import Article
from app.schema import ArticleSchema
from app.util import get_base_url, setCookie
from . import main_bp
from flask import current_app as app

@main_bp.route("/", methods=["GET"])
def index():
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
    setCookie(response,'Session-ID',session.client_session_id)
    setCookie(response,'Session-SALT',session.salt,httponly=False)

    return response

@main_bp.route('/login')
def loginPage():
    response = make_response(render_template('login.html'))

    session_ID = request.cookies.get('Session-ID')

    if session_ID is not None:
        session = Client.query.filter_by(client_session_id = session_ID).first()
        if session is not None:
            if session.isValid():
                response.set_cookie('Session-ID', session.client_session_id, httponly=True, max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
                response.set_cookie('Session-SALT', session.salt,  max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
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
    response.set_cookie('Session-ID', session.client_session_id, httponly=True, max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
    response.set_cookie('Session-SALT', session.salt,  max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
    return response



@main_bp.route('/home')
@verify_user
def homePage(session):
    response = make_response(render_template('home.html'))
    response.set_cookie('Session-ID', session.client_session_id, httponly=True, max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
    response.set_cookie('Session-SALT', session.salt,  max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
    return response


@main_bp.route('/repository')
@verify_session
def repositoryPage(session):
    page = request.args.get('page', 1, type=int)
    entry = request.args.get('entry', 10, type=int)


    

    server_url = get_base_url()
    # server_url = "http://127.0.0.1:5012"
    url = f"{server_url}/researchrepository/api/article/table"
    
    headers = {
        "API-ID":app.config.get('API_ID')
    }
    
    cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary
    params = {
        'page': page,
        'entry': entry
    }

    response = requests.get(url, headers=headers, cookies=cookies,params=params)  # Use `requests.get`

    if response.status_code==200:
        data =  response.json()
        articles = data["data"]
        total_pages = data["total_pages"]
        
        response = make_response(render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages))
        response.set_cookie('Session-ID', session.client_session_id, httponly=True, max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
        response.set_cookie('Session-SALT', session.salt,  max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
        return response
    else:
        return jsonify({"message":"Something went wrong"}),500


@main_bp.route('/article/<string:id>')
@verify_session
def articlePage(session,id):
    server_url = get_base_url()
    url = f"{server_url}/researchrepository/api/article/{id}"
    headers = {
        "API-ID":app.config.get('API_ID')
    }
    
    cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

    response = requests.get(url, headers=headers, cookies=cookies)  # Use `requests.get`

    if response.status_code==200:
        article_data = response.json()

        
        response = make_response(render_template('article.html',article=article_data))
        response.set_cookie('Session-ID', session.client_session_id, httponly=True, max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
        response.set_cookie('Session-SALT', session.salt,  max_age=app.config['COOKIE_AGE'], secure = True, samesite='None')  # expires in 1 day
        return response
    else:
        return jsonify({"message":f"Article id {id} not found"}),404


@main_bp.route('/constant/<path:filename>')
def style_css(filename):
    return send_from_directory('static', filename)

