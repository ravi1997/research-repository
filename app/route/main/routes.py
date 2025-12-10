import math
from pprint import pprint
from flask import jsonify, render_template,make_response, request,current_app
import requests
from concurrent.futures import ThreadPoolExecutor
from flask_caching import Cache
from tenacity import retry, stop_after_attempt, wait_fixed
from app.extension import db,cache
import re
from time import time
from datetime import datetime

from app.decorator import verify_FACULTY_role, verify_LIBRARYMANAGER_role, verify_duplicate_roles, verify_edit_roles, verify_ownership_roles, verify_session, verify_user
from app.models import Client
from app.models.user import UserRole
from app.models.article import *
from app.mylogger import error_logger
from app.utility import get_base_url
from app.session import settingSession
from app.route.main import main_bp
from flask import current_app as app
from app.schema import ArticleSchema, UserSchema
 

user_schema = UserSchema() 

def getRole(user):
	roles = []

	if user:
		if user.has_role(UserRole.SUPERADMIN):
			roles.append("SUPERADMIN")

		if user.has_role(UserRole.LIBRARYMANAGER):
			roles.append("LIBRARYMANAGER")

		if user.has_role(UserRole.FACULTY):
			roles.append("FACULTY")

		if user.has_role(UserRole.SCIENTIST):
			roles.append("SCIENTIST")

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
				response = make_response(render_template('index.html',roles = getRole(session.user),logged_in=True,user = user_schema.dump(session.user)))
				return settingSession(request,response)
	response = make_response(render_template('index.html', roles = getRole(None),logged_in=False))
	return settingSession(request,response)



@main_bp.route('/dashboard')
def dashboard():
	total_authors = db.session.query(func.count(func.distinct(Author.employee_id))).scalar()
	total_articles = Article.query.count()
	total_keywords = db.session.query(func.count(Keyword.id)).scalar()
	total_views = db.session.query(func.sum(ArticleStatistic.viewed)).scalar() or 0

	top_viewed_articles = db.session.query(
		Article.title,
		func.sum(ArticleStatistic.viewed).label('views')
	).join(ArticleStatistic, Article.id == ArticleStatistic.article_id)\
	.group_by(Article.id)\
	.order_by(func.sum(ArticleStatistic.viewed).desc())\
	.limit(5).all()

	keyword_usage = db.session.query(
		Keyword.keyword,
		func.count(Article.id).label('usage')
	).join(ArticleKeyword, ArticleKeyword.keyword_id == Keyword.id)\
	.join(Article, Article.id == ArticleKeyword.article_id)\
	.group_by(Keyword.id)\
	.order_by(func.count(Article.id).desc())\
	.limit(5).all()

	top_authors = db.session.query(
		Author.fullName,
		func.count(Article.id).label('article_count')
	).join(ArticleAuthor, ArticleAuthor.author_id == Author.id) \
	.join(Article, Article.id == ArticleAuthor.article_id) \
	.group_by(Author.id)  \
	.order_by(func.count(Article.id).desc()) \
	.limit(5).all()

	article_trends = db.session.query(
		func.to_char(Article.created_at, 'YYYY-MM').label('month'),
		func.count(Article.id).label('article_count')
	).group_by(func.to_char(Article.created_at, 'YYYY-MM'))\
	.order_by('month')\
	.all()

	session_id = request.cookies.get('Session-ID')
	user_info = None
	roles = getRole(None)
	logged_in = False

	if session_id:
		session = Client.query.filter_by(client_session_id=session_id).first()
		if session and session.isValid() and session.user_id:
			user_info = user_schema.dump(session.user)
			roles = getRole(session.user)
			logged_in = True

	response = make_response(render_template(
		'dashboard.html',
		total_authors=total_authors,
		total_articles=total_articles,
		total_keywords=total_keywords,
		total_views=total_views,
		top_viewed_articles=top_viewed_articles,
		keyword_usage=keyword_usage,
		top_authors=top_authors,
		article_trends=article_trends,
		roles=roles,
		logged_in=logged_in,
		user=user_info
	))
	return settingSession(request, response)


@main_bp.route('/login')
def loginPage():
	session_id = request.cookies.get('Session-ID')

	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				user_info = user_schema.dump(session.user)
				return render_template('home.html',roles = getRole(session.user),logged_in=True,
						user=user_info   
						   )
	response = make_response(render_template('login.html', roles = getRole(None),logged_in=False))
	return settingSession(request,response)

@main_bp.route('/home')
def homePage():
	session_id = request.cookies.get('Session-ID')
	if session_id is not None:   
		session = Client.query.filter_by(client_session_id=session_id).first()

		if session is not None:
			if session.isValid() and session.user_id is not None:
				roles = getRole(session.user)
				if roles == []:
					return render_template('index.html',roles = getRole(session.user),logged_in=True,user = user_schema.dump(session.user))
					
				return render_template('home.html',roles = getRole(session.user),logged_in=True,user = user_schema.dump(session.user))
	
	response = make_response(render_template('login.html', roles = getRole(None),logged_in=False))
	return settingSession(request,response)


@main_bp.route('/repository')
def repositoryPage():
	page = request.args.get('page', 1, type=int)
	entry = request.args.get('entry', 10, type=int)

	server_url = get_base_url()
	url = f"{server_url}/api/article/table"
	
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	if request.cookies:	
		cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary
	else:
		cookies = requests.get(f"{server_url}/api/public/generateSession", headers=headers).json()

 
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
					return render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages,roles = getRole(session.user),logged_in=True,user = user_schema.dump(session.user))

		response = make_response(render_template('repository.html',articles=articles,current_page=page,entry=entry,total_pages = total_pages,roles = getRole(None),logged_in=False))
		return settingSession(request,response)
	else:
		error_logger.info(response.json())
		return jsonify({"message":"Something went wrong"}),500


def process_search_results(results):
	"""
	Processes and removes duplicates from the search results.

	Args:
		results (list): List of articles fetched from the external API.

	Returns:
		list: List of unique articles based on their UUID.
	"""
	current_app.logger.info("Starting to process search results...")

	# Merge the articles from different search results
	articles_json = []
	for result in results:
		if result and 'articles' in result:
			articles_json.extend(result['articles'])
	
	current_app.logger.info(f"Total articles fetched: {len(articles_json)}")

	# Remove duplicates based on UUID
	unique_articles = {article['uuid']: article for article in articles_json}
	current_app.logger.info(f"Unique articles after removing duplicates: {len(unique_articles)}")
	
	return list(unique_articles.values())

def filter_articles(articles, search_params):
	"""
	Filters the articles based on provided search parameters.

	Args:
		articles (list): List of articles to filter.
		search_params (dict): Dictionary containing filter parameters such as authors, keywords, date range, etc.

	Returns:
		list: List of filtered articles.
	"""
	current_app.logger.info("Starting to filter articles...")

	filtered_articles = articles
	filter_json = {}

	# Apply author filters
	if 'authors' in search_params:
		authors_filter = set(search_params['authors'])
		filter_json["authors"]=authors_filter
		filtered_articles = [article for article in filtered_articles if any(author['fullName'] in authors_filter for author in article['authors'])]
		current_app.logger.info(f"Applied author filter, articles left: {len(filtered_articles)}")

	# Apply keyword filters
	if 'keywords' in search_params:
		keywords_filter = set(search_params['keywords'])
		filter_json["keywords"] = keywords_filter
		filtered_articles = [article for article in filtered_articles if any(keyword['keyword'] in keywords_filter for keyword in article['keywords'])]
		current_app.logger.info(f"Applied keyword filter, articles left: {len(filtered_articles)}")

	# Apply start and end date filters
	if 'start_date' in search_params and search_params['start_date'] and search_params['start_date'][0]!='':
		filter_json["start_date"] = search_params['start_date']
		start_date = datetime.strptime(search_params['start_date'][0], '%Y-%m-%d')
		filtered_articles = [article for article in filtered_articles if datetime.strptime(article['publication_date'], '%Y-%m-%d') >= start_date]
		current_app.logger.info(f"Applied start date filter, articles left: {len(filtered_articles)}")

	if 'end_date' in search_params and search_params['end_date'] and search_params['end_date'][0]!='':
		filter_json["end_date"] = search_params['end_date']
		end_date = datetime.strptime(search_params['end_date'][0], '%Y-%m-%d')
		filtered_articles = [article for article in filtered_articles if datetime.strptime(article['publication_date'], '%Y-%m-%d') <= end_date]
		current_app.logger.info(f"Applied end date filter, articles left: {len(filtered_articles)}")

	# Apply journal filters
	if 'journals' in search_params:
		journals_filter = set(search_params['journals'])
		filter_json["journals"] = journals_filter
		filtered_articles = [article for article in filtered_articles if article['journal'] in journals_filter]
		current_app.logger.info(f"Applied journal filter, articles left: {len(filtered_articles)}")

	return filtered_articles,filter_json

def paginate_articles(filtered_articles, offset, limit):
	"""
	Paginates the filtered articles.

	Args:
		filtered_articles (list): List of filtered articles.
		offset (int): The starting index for pagination.
		limit (int): The number of articles to return per page.

	Returns:
		list: A subset of filtered articles for the current page.
	"""
	current_app.logger.info(f"Paginating articles, offset: {offset}, limit: {limit}")
	return filtered_articles[offset:offset + limit]


@main_bp.route('/search')
def searchPageCopy():
	# If there are any query parameters, call the external search API
	search_params = request.args.to_dict(flat=False)
	app.logger.info(f"Searching : {search_params}. Fetching results...")
	# Prepare the server URL and endpoint
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 10, type=int)
	current_page=(offset//limit) + 1
	entry=limit
	filter_json = {}
	# Apply filters for authors

	if 'authors' in search_params:
		filter_json["authors"] = search_params['authors']

	# Apply filters for keywords
	if 'keywords' in search_params:
		filter_json["keywords"] = search_params['keywords']

	# Apply filters for publication date
	if 'start_date' in search_params:
		if search_params['start_date'] and search_params['start_date']!="":
			filter_json["start_date"] = search_params['start_date']

	if 'end_date' in search_params:
		if search_params['end_date'] and search_params['end_date']!="":
			filter_json["end_date"] = search_params['end_date']

	# Apply filters for journals
	if 'journals' in search_params:
		filter_json["journals"] = search_params['journals']	# Apply filters for authors

	
	session_id = request.cookies.get('Session-ID')
	if session_id is not None:   
			session = Client.query.filter_by(client_session_id=session_id).first()

			if session is not None:
				if session.isValid() and session.user_id is not None:
					return render_template(
						'search.html',
						query=search_params['query'][0],
						myfilters = filter_json,
						current_page=current_page,
						offset = offset,
						entry=entry,
						roles = getRole(session.user),
						logged_in=session.user_id is not None,
						user = user_schema.dump(session.user) if session.user_id is not None else {}
					)
	
	response = make_response(render_template('search.html',
						query=search_params['query'][0],
						myfilters = filter_json,
						current_page=current_page,
						offset = offset,
						entry=entry,roles = getRole(None),logged_in=False))
	return settingSession(request,response)

# @main_bp.route('/search')
# @verify_session
# def searchPage(session):
# 	# If there are any query parameters, call the external search API
# 	search_params = request.args.to_dict(flat=False)
# 	app.logger.info(f"Searching : {search_params}. Fetching results...")
# 	# Prepare the server URL and endpoint
# 	server_url = get_base_url()
# 	url = f"{server_url}/api/search/search"

# 	# Prepare headers (you can adjust this according to your API needs)
# 	headers = {
# 		"API-ID": app.config.get('API_ID')  # Assuming the API_ID is set in your Flask config
# 	}

# 	# Prepare cookies from the current request
# 	cookies = request.cookies.to_dict()  # Converts ImmutableMultiDict to a regular dict

# 	# Send the GET request to the external search API
# 	response = requests.get(url, headers=headers, cookies=cookies, params=search_params)

# 	# Check if the response is successful
# 	if response.status_code == 200:
# 		# Parse the JSON response
# 		search_results = response.json()
# 		# Render the search page with the results from the external API
# 		current_page=(search_results["offset"]//search_results["limit"]) + 1
# 		entry=search_results["limit"]
# 		total_pages = math.ceil(search_results["total_articles"]/search_results["limit"])
# 		app.logger.info(f"total_pages : {total_pages}")
# 		articles= []
# 		for uuid in search_results['articles']:
# 			article = Article.query.filter_by(uuid=uuid).first()
# 			if article:
# 				articles.append(ArticleSchema().dump(article))
# 		return render_template(
# 			'search.html',
# 			query=search_params['query'][0],
# 			myfilters = search_results["filters"],
# 			articles=articles,
#    			current_page=current_page,
# 	  		offset = search_results["offset"],
# 	  		entry=entry,
# 			total_pages = total_pages,
#    			roles = getRole(session.user),
# 			logged_in=session.user_id is not None,
# 			user = user_schema.dump(session.user) if session.user_id is not None else {}
# 		)
# 	else:
# 		app.logger.info(f"status code : {response.status_code}")
# 		return jsonify({"error": "Failed to fetch search results from external API"}), 500


@main_bp.route('/ownershipresult')
@verify_ownership_roles
def ownershipresultPage(session):
	search_params = request.args.to_dict(flat=False)
	app.logger.info(f"Searching : {search_params}. Fetching results...")
	# Prepare the server URL and endpoint
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 10, type=int)
	current_page=(offset//limit) + 1
	entry=limit
	filter_json = {}
	# Apply filters for authors

	if 'authors' in search_params:
		filter_json["authors"] = search_params['authors']

	# Apply filters for keywords
	if 'keywords' in search_params:
		filter_json["keywords"] = search_params['keywords']

	# Apply filters for publication date
	if 'start_date' in search_params:
		if search_params['start_date'] and search_params['start_date']!="":
			filter_json["start_date"] = search_params['start_date']

	if 'end_date' in search_params:
		if search_params['end_date'] and search_params['end_date']!="":
			filter_json["end_date"] = search_params['end_date']

	# Apply filters for journals
	if 'journals' in search_params:
		filter_json["journals"] = search_params['journals']	# Apply filters for authors

 
	return render_template(
		'ownershipresult.html',
		query=search_params['query'][0],
		myfilters = filter_json,
		current_page=current_page,
		offset = offset,
		entry=entry,
		roles = getRole(session.user),
		logged_in=session.user_id is not None,
		user = user_schema.dump(session.user) if session.user_id is not None else {}
	)

@main_bp.route('/ownership')
@verify_ownership_roles
def ownershipPage(session):
	
	response = make_response(render_template('ownership.html',roles = getRole(session.user),logged_in=True,user = user_schema.dump(session.user)))
	return settingSession(request,response)



@main_bp.route('/article/<string:id>')
@verify_session
def articlePage(session,id):
	server_url = get_base_url()
	url = f"{server_url}/api/article/{id}"
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
				logged_in=userlogged,
				user = user_schema.dump(session.user) if session.user_id is not None else {}
			)
	else:
		app.logger.info(response.json())
		app.logger.info(response.status_code)
		return jsonify({"message":f"Article id {id} not found"}),404

@main_bp.route('/article/edit/<string:id>')
@verify_edit_roles
def editArticlePage(session,id):
	server_url = get_base_url()
	url = f"{server_url}/api/article/{id}"
	headers = {
		"API-ID":app.config.get('API_ID')
	}
	
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		article_data = response.json()
		return render_template('edit_article.html',article=article_data,
				roles = getRole(session.user),
				logged_in=session.user_id is not None,
				user = user_schema.dump(session.user) if session.user_id is not None else {}
	)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404


@main_bp.route('/duplicate/<string:field>')
@verify_duplicate_roles
def duplicateByPage(session,field):
	server_url = get_base_url()
	url = f"{server_url}/api/article/duplicates"
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
		return render_template('duplicate.html',results=results[field],duplicateBy=duplicateBy[field],roles = getRole(session.user),logged_in=session.user_id is not None,user = user_schema.dump(session.user) if session.user_id is not None else {})
	else:
		app.logger.info(f"status code : {response.status_code}")
		return jsonify({"message":f"Article {id} not found"}),404

@main_bp.route('/singleDuplicate/<string:id>')
@verify_duplicate_roles
def singleArticleDuplicatePage(session,id):
	server_url = get_base_url()
	url = f"{server_url}/api/article/duplicate/{id}"
	headers = {
		"API-ID":app.config.get('API_ID')
	}
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	response = requests.get(url, headers=headers, cookies=cookies)  # Use `requests.get`

	if response.status_code==200:
		result = response.json()
		articles = []
		for uuid in result["articles"]:
			article_url = f"{server_url}/api/article/{uuid}"
			new_response = requests.get(article_url, headers=headers, cookies=cookies)  # Use `requests.get`
			article = new_response.json()
			articles.append(article)
		return render_template('singleDuplicate.html',uuid = id, result=result,articles = articles,roles = getRole(session.user),logged_in=session.user_id is not None,user = user_schema.dump(session.user) if session.user_id is not None else {})
	else:
		return jsonify({"message":f"Duplicate id {id} not found"}),404

@main_bp.route('/author')
@verify_session
def authorPage(session):
	query = request.args.get('q','')
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 100, type=int)
	
	server_url = get_base_url()
	url = f"{server_url}/api/article/search"
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
		return render_template('author.html',articles=results["articles"],result_for=results["result_for"],roles = getRole(session.user),logged_in=session.user_id is not None,user = user_schema.dump(session.user) if session.user_id is not None else {})
	else:
		return jsonify({"message":f"Internal Error occured"}),500

@main_bp.route('/keyword')
@verify_session
def keywordPage(session):
	query = request.args.get('q','')
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 100, type=int)
	
	server_url = get_base_url()
	url = f"{server_url}/api/article/search"
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
		return render_template('keyword.html',articles=results["articles"],result_for=results["result_for"],logged_in=session.user_id is not None,user = user_schema.dump(session.user) if session.user_id is not None else {})
	else:
		return jsonify({"message":f"Internal Error occured"}),500

@main_bp.route('/journal')
@verify_session
def journalPage(session):
	query = request.args.get('q','')
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 100, type=int)
	
	server_url = get_base_url()
	url = f"{server_url}/api/article/search"
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
		return render_template('journal.html',articles=results["articles"],result_for=results["result_for"],logged_in=session.user_id is not None,user = user_schema.dump(session.user) if session.user_id is not None else {})
	else:
		return jsonify({"message":f"Internal Error occured"}),500

