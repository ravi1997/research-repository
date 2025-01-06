import math
from flask import jsonify, render_template,make_response, request
import requests

from time import time


from app.decorator import verify_FACULTY_role, verify_LIBRARYMANAGER_role, verify_session, verify_user
from app.models import Client
from app.models.user import UserRole
from app.mylogger import error_logger
from app.util import get_base_url
from app.session import settingSession
from app.route.main import main_bp
from flask import current_app as app


def getRole(user):
	roles = []

	if user:
		if user.has_role(UserRole.SUPERADMIN):
			roles.append("SUPERADMIN")

		if user.has_role(UserRole.LIBRARYMANAGER):
			roles.append("LIBRARYMANAGER")

		if user.has_role(UserRole.FACULTY):
			roles.append("FACULTY")

		if user.has_role(UserRole.RESIDENT):
			roles.append("RESIDENT")

	return roles

@main_bp.route("/", methods=["GET"])
def index():
	session_id = request.cookies.get('Session-ID')
	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				response = make_response(render_template('index.html',roles = getRole(session.user),logged_in=True))
				return settingSession(request,response)
	response = make_response(render_template('index.html', roles = getRole(None),logged_in=False))
	return settingSession(request,response)

@main_bp.route('/login')
def loginPage():
	session_id = request.cookies.get('Session-ID')

	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				return render_template('home.html',roles = getRole(session.user),logged_in=True)
	response = make_response(render_template('login.html', roles = getRole(None),logged_in=False))
	return settingSession(request,response)

@main_bp.route('/home')
def homePage():
	session_id = request.cookies.get('Session-ID')
	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				return render_template('home.html',roles = getRole(session.user),logged_in=True)
	
	response = make_response(render_template('login.html', roles = getRole(None),logged_in=False))
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
					return render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages,roles = getRole(session.user),logged_in=True)

		response = make_response(render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages,roles = getRole(None),logged_in=False))
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
   			roles = getRole(session.user),
			logged_in=session.user_id is not None
		)
	else:
		# If the external API request fails, return an error page or message
		return jsonify({"error": "Failed to fetch search results from external API"}), 500


@main_bp.route('/ownershipresult')
@verify_FACULTY_role
def ownershipresultPage(session):
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
			'ownershipresult.html',
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
   			roles = getRole(session.user),
			logged_in=session.user_id is not None
		)
	else:
		# If the external API request fails, return an error page or message
		return jsonify({"error": "Failed to fetch search results from external API"}), 500


@main_bp.route('/ownership')
@verify_FACULTY_role
def ownershipPage(session):
	
	response = make_response(render_template('ownership.html',roles = getRole(session.user),logged_in=True))
	return settingSession(request,response)



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
		return render_template('article.html',
				article=article_data,
				roles = getRole(session.user),
				logged_in=userlogged
			)
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
		return render_template('edit_article.html',article=article_data,
				roles = getRole(session.user),
				logged_in=session.user_id is not None)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404


@main_bp.route('/duplicate/<string:field>')
@verify_LIBRARYMANAGER_role
def duplicateByPage(session,field):
	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/duplicates"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	params = {
		"field":field
	}	
	duplicateBy = {
		"title":"Title",
		"pubmed_id":"PUBMED ID",
		"pmc_id":"PMC ID",
		"doi":"DOI"
	}

	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('duplicate.html',results=results[field],duplicateBy=duplicateBy[field],roles = getRole(session.user),logged_in=session.user_id is not None)
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
		return render_template('singleDuplicate.html',uuid = id, result=result,articles = articles,roles = getRole(session.user),logged_in=session.user_id is not None)
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
		"search_by":"employee",
		"offset":offset,
		"limit":limit
	}	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary
	response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		results = response.json()
		return render_template('author.html',results=results["articles"],result_for=results["result_for"],roles = getRole(session.user),logged_in=session.user_id is not None)
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

