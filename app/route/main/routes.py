from datetime import datetime
from pprint import pprint
import uuid
from flask import jsonify, render_template,make_response, request, send_from_directory
import requests

from app.decorator import verify_session, verify_user
from app.models import Client
from app.extension import db
from app.models.article import Article
from app.schema import ArticleSchema
from app.util import get_base_url, getIP, setCookie
from app.session import settingSession
from . import main_bp
from flask import current_app as app

@main_bp.route("/", methods=["GET"])
def index():
	response = make_response(render_template('index.html'))
	return settingSession(request,response)

@main_bp.route('/login')
def loginPage():
	session_id = request.cookies.get('Session-ID')

	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				return render_template('home.html')
	response = make_response(render_template('login.html'))
	return settingSession(request,response)



@main_bp.route('/home')
def homePage():
	session_id = request.cookies.get('Session-ID')
	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				return render_template('home.html')
	
	response = make_response(render_template('login.html'))
	return settingSession(request,response)


@main_bp.route('/repository')
def repositoryPage():
	page = request.args.get('page', 1, type=int)
	entry = request.args.get('entry', 10, type=int)

	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/table"
	
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	if request.cookies:	
		cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary
	else:
		cookies = requests.get(f"{server_url}/researchrepository/api/public/generateSession", headers=headers).json()

 
	params = {
		'page': page,
		'entry': entry
	}

	response = requests.get(url, headers=headers, cookies=cookies,params=params)  # Use `requests.get`

	if response.status_code==200:
		data =  response.json()
		articles = data["data"]
		total_pages = data["total_pages"]

		session_id = request.cookies.get('Session-ID')
		if session_id is not None:   
			session = Client.query.filter_by(client_session_id=session_id).first()

			if session is not None:
				if session.isValid() and session.user_id is not None:
					return render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages)

		response = make_response(render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages))
		return settingSession(request,response)
	else:
		pprint(response.json())
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


	userlogged = session.user_id is not None

	if response.status_code==200:
		article_data = response.json()
		return render_template('article.html',article=article_data,edit=userlogged)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404



@main_bp.route('/article/edit/<string:id>')
@verify_user
def editArticlePage(session,id):
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/{id}"
	headers = {
		"API-ID":app.config.get('API_ID')
	}
	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		article_data = response.json()
		return render_template('edit_article.html',article=article_data)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404


@main_bp.route('/constant/<path:filename>')
def style_css(filename):
	return send_from_directory('static', filename)

