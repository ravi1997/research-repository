from datetime import datetime
import math
from pprint import pprint
import uuid
from flask import jsonify, render_template,make_response, request, send_from_directory
import requests

from time import time


from app.decorator import verify_LIBRARYMANAGER_role, verify_session, verify_user
from app.models import Client
from app.extension import db
from app.mylogger import error_logger
from app.models.article import Article
from app.schema import ArticleSchema
from app.util import get_base_url, getIP, setCookie
from app.session import settingSession
from . import main_bp
from flask import current_app as app




@main_bp.route("/", methods=["GET"])
def index():
	session_id = request.cookies.get('Session-ID')
	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				response = make_response(render_template('index.html',time=time(),logged_in=session.user_id is not None))
				return settingSession(request,response)
	response = make_response(render_template('index.html', time=time()))
	return settingSession(request,response)

@main_bp.route('/login')
def loginPage():
	session_id = request.cookies.get('Session-ID')

	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				return render_template('home.html',logged_in=session.user_id is not None)
	response = make_response(render_template('login.html'))
	return settingSession(request,response)



@main_bp.route('/home')
def homePage():
	session_id = request.cookies.get('Session-ID')
	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				return render_template('home.html',logged_in=True)
	
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
					return render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages,logged_in=True)

		response = make_response(render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages))
		return settingSession(request,response)
	else:
		error_logger.info(response.json())
		return jsonify({"message":"Something went wrong"}),500

@main_bp.route('/search')
@verify_session
def searchPage(session):
	# If there are any query parameters, call the external search API
	search_params = request.args.to_dict(flat=False)

	# Prepare the server URL and endpoint
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/searchspecific"

	# Prepare headers (you can adjust this according to your API needs)
	headers = {
		"API-ID": app.config.get('API_ID')  # Assuming the API_ID is set in your Flask config
	}

	# Prepare cookies from the current request
	cookies = request.cookies.to_dict()  # Converts ImmutableMultiDict to a regular dict

	# Send the GET request to the external search API
	response = requests.get(url, headers=headers, cookies=cookies, params=search_params)

	# Check if the response is successful
	if response.status_code == 200:
		# Parse the JSON response
		search_results = response.json()
		# Render the search page with the results from the external API
		current_page=(search_results["offset"]//search_results["limit"]) + 1
		entry=search_results["limit"]
		total_pages = math.ceil(search_results["total_articles"]/search_results["limit"])
  
		return render_template(
			'search.html',
			query=search_params['query'][0],
			myfilters = search_results["filters"],
			articles=search_results['articles'],
			unique_authors=search_results['unique_authors'],
			unique_keywords=search_results['unique_keywords'],
			unique_journals=search_results['unique_journals'],
   			current_page=current_page,
      		offset = search_results["offset"],
	  		entry=entry,
			total_pages = total_pages,
			logged_in=session.user_id is not None
		)
	else:
		# If the external API request fails, return an error page or message
		return jsonify({"error": "Failed to fetch search results from external API"}), 500
	# If no parameters are provided, render the page with empty filter options


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
		return render_template('article.html',article=article_data,edit=userlogged,logged_in=session.user_id is not None)
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
		return render_template('edit_article.html',article=article_data,logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404


@main_bp.route('/duplicate-by-title')
@verify_LIBRARYMANAGER_role
def duplicateByTitlePage(session):
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/duplicates"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	params = {
		"field":"title"
	}	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('duplicate.html',results=results["title"],duplicateBy="Title",logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404

@main_bp.route('/singleDuplicate/<string:id>')
@verify_LIBRARYMANAGER_role
def singleArticleDuplicatePage(session,id):
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/duplicate/{id}"
	headers = {
		"API-ID":app.config.get('API_ID')
	}
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		result = response.json()
		articles = []
		for uuid in result["articles"]:
			article_url = f"{server_url}/researchrepository/api/article/{uuid}"
			new_response = requests.get(article_url, headers=headers, cookies=cookies)  # Use `requests.get`
		
			article = new_response.json()
			articles.append(article)
  
		return render_template('singleDuplicate.html',uuid = id, result=result,articles = articles,logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Duplicate id {id} not found"}),404



@main_bp.route('/duplicate-by-pubmed-id')
@verify_LIBRARYMANAGER_role
def duplicateByPubmedIDPage(session):
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/duplicates"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	params = {
		"field":"pubmed_id"
	}	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('duplicate.html',results=results["pubmed_id"],duplicateBy="PUBMED ID",logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404

@main_bp.route('/duplicate-by-pmc-id')
@verify_LIBRARYMANAGER_role
def duplicateByPMCIDPage(session):
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/duplicates"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	params = {
		"field":"pmc_id"
	}	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('duplicate.html',results=results["pmc_id"],duplicateBy="PMC ID",logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404


@main_bp.route('/duplicate-by-doi')
@verify_LIBRARYMANAGER_role
def duplicateByDOIPage(session):
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/duplicates"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	params = {
		"field":"doi"
	}	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('duplicate.html',results=results["doi"],duplicateBy="DOI",logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Duplicate id {id} not found"}),404


@main_bp.route('/author')
@verify_session
def authorPage(session):
	query = request.args.get('q','')
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 10, type=int)
	
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/search"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	params = {
		"q":query,
		"search_by":"author",
		"offset":offset,
		"limit":limit
	}	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary
	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('author.html',results=results["articles"],result_for=results["result_for"],logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Internal Error occured"}),500

@main_bp.route('/keyword')
@verify_session
def keywordPage(session):
	query = request.args.get('q','')
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 10, type=int)
	
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/search"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	params = {
		"q":query,
		"search_by":"keyword",
		"offset":offset,
		"limit":limit
	}	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary
	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('keyword.html',results=results["articles"],result_for=results["result_for"],logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Internal Error occured"}),500


@main_bp.route('/journal')
@verify_session
def journalPage(session):
	query = request.args.get('q','')
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 10, type=int)
	
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/searchspec"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	params = {
		"q":query,
		"search_by":"journal",
		"offset":offset,
		"limit":limit
	}	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary
	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('journal.html',results=results["articles"],result_for=results["result_for"],logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Internal Error occured"}),500

