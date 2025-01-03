from datetime import date, datetime, timedelta
from multiprocessing import Pool
import os
from pprint import pprint
import traceback
from flask import jsonify,current_app as app, request
from marshmallow import ValidationError
import requests
from sqlalchemy import desc, or_
from sqlalchemy.orm import aliased
import uuid
from sqlalchemy import select, or_
from sqlalchemy.orm import joinedload
from itertools import combinations

from sqlalchemy import func
from collections import defaultdict
from app.decorator import checkBlueprintRouteFlag, verify_LIBRARYMANAGER_role, verify_SUPERADMIN_role, verify_USER_role, verify_body, verify_internal_api_id, verify_session
from app.extension import db,scheduler
from app.models.article import Article, ArticleAuthor, ArticleKeyword, ArticlePublicationType, ArticleStatistic, Author, DeletedArticle, Duplicate, Keyword, Link, PublicationType
from app.schema import ArticleSchema, AuthorSchema, AuthorSchemaWithoutArticle, DuplicateSchema, KeywordSchema, KeywordSchemaWithoutArticle, LinkSchema, PublicationTypeSchema
from app.util import download_xml, fileReader, find_full_row_match, get_base_url, getUnique,  parse_pubmed_xml
from . import article_bp
import re

@article_bp.route("/")
@checkBlueprintRouteFlag
@verify_SUPERADMIN_role
def index(session):
	return "This is The research repository article route"

@article_bp.route("/table")
@verify_session
@verify_internal_api_id
def generateTable(session):
	page = request.args.get('page', 1, type=int)
	per_page = request.args.get('entry', 10, type=int)
	start = (page - 1) * per_page
	
	total = Article.query.count()
	articles_schema = ArticleSchema(many=True)
	articles = Article.query.order_by(Article.publication_date.desc()).offset(start).limit(per_page).all()
	datas = articles_schema.dump(articles)
		
	return jsonify({
		'data': datas,
		'page': page,
		'total_pages': total // per_page + (1 if total % per_page > 0 else 0)
	})

@article_bp.route("/<string:id>")
@verify_session
@verify_internal_api_id
def getSingle_article(session,id):
	article = Article.query.filter_by(uuid=id).first()
	if article:
		article_schema = ArticleSchema()
		return article_schema.dump(article),200
	else:
		return jsonify({"message":f"Article id {id} not found"}),404


def check_duplicates(article_data):
	"""
	Check for duplicates in the database using a single query.
	"""
	filters = []
	if 'title' in article_data and article_data['title'] is not None:
		filters.append(Article.title == article_data['title'])
	if 'pubmed_id' in article_data and article_data['pubmed_id'] is not None:
		filters.append(Article.pubmed_id == article_data['pubmed_id'])
	if 'doi' in article_data and article_data['doi'] is not None:
		filters.append(Article.doi == article_data['doi'])
	if 'pmc_id' in article_data and article_data['pmc_id'] is not None:
		filters.append(Article.pmc_id == article_data['pmc_id'])

	if not filters:
		return None
	
	return Article.query.filter(or_(*filters)).first()


def add_or_get(model, session, **kwargs):
	"""
	Add a new record or get an existing one.
	"""
	instance = db.session.query(model).filter_by(**kwargs).first()
	if instance:
		return instance
	instance = model(**kwargs)
	db.session.add(instance)
	db.session.commit()  # Assign ID without committing
	return instance


def upload(session, request, ALLOWED_EXTENSIONS):
	if 'file' not in request.files:
		return jsonify({"error": "No file part in the request"}), 400

	file = request.files['file']

	if file.filename == '':
		return jsonify({"error": "No file selected"}), 400

	if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
		filename = file.filename
		file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

		# Save the file
		file.save(file_path)

		myjsons, skipped = fileReader(filepath=file_path)
		article_schema = ArticleSchema()
		result_ids = []
		duplicates = {"title": [], "pubmed_id": [], "doi": [], "pmc_id": []}
		duplicate_count = 0

		try:
			for myjson in myjsons:
				temp_json = myjson.copy()

				publication_types = temp_json.pop('publication_types', [])
				keywords = temp_json.pop('keywords', [])
				authors = temp_json.pop('authors', [])
				links = temp_json.pop('links', [])

				# Check for duplicates
				duplicate_article = check_duplicates(temp_json)
				if duplicate_article:
					duplicate_count += 1
					if duplicate_article.title is not None and duplicate_article.title == myjson['title']:
						duplicates['title'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
					elif duplicate_article.pubmed_id is not None and duplicate_article.pubmed_id == myjson['pubmed_id']:
						duplicates['pubmed_id'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
					elif duplicate_article.doi is not None and duplicate_article.doi == myjson['doi']:
						duplicates['doi'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
					elif duplicate_article.pmc_id is not None and duplicate_article.pmc_id == myjson['pmc_id']:
						duplicates['pmc_id'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})

					continue
 
				# Create new article
				new_article = article_schema.load(temp_json)
				db.session.add(new_article)
				db.session.commit()  # Get article ID

				# Add publication types
				for pub_type in publication_types:
					pub_instance = add_or_get(PublicationType, session, publication_type=pub_type['publication_type'])
					new_article.publication_types.append(pub_instance)

				# Add keywords
				for keyword in set(kw['keyword'] for kw in keywords):  # Avoid duplicates in the same article
					keyword_instance = add_or_get(Keyword, session, keyword=keyword)
					new_article.keywords.append(keyword_instance)

				# Add links
				for link in links:
					new_link = Link(**link)
					db.session.add(new_link)
					new_article.links.append(new_link)

				db.session.commit()
				for idx, author in enumerate(authors):
					author_instance = add_or_get(Author, session, **author)
					new_article.authors.append(ArticleAuthor(author=author_instance, sequence_number=idx + 1))

				db.session.commit()
				result_ids.append(new_article.id)

			articles = Article.query.filter(Article.id.in_(result_ids)).all()
			return jsonify({
				"message": "File uploaded successfully",
				"filename": filename,
				"added_articles": len(result_ids),
				"skipped_articles": skipped,
				"articles": ArticleSchema(many=True).dump(articles),
				"duplicate_articles": duplicates,
			}), 200

		except Exception as e:
			app.logger.error(f"Error during file processing: {str(e)}")
			traceback.print_exc()
			return jsonify({"error": "An error occurred while processing the file"}), 500

	return jsonify({"error": "Invalid file type. Only .ris files are allowed."}), 401

@article_bp.route('/upload_ris', methods=['POST'])
@verify_USER_role
def upload_ris(session):
	return upload(session,request,['ris'])

@article_bp.route('/upload_nbib', methods=['POST'])
@verify_USER_role
def upload_nbib(session):
	return upload(session,request,['nbib'])

@article_bp.route('/pubmedFectch', methods=['POST'])
@verify_USER_role
@verify_body
def pubmedFectch(data,session):
	pubmed_id = data["pmid"]

	filename = os.path.join(app.config["UPLOAD_FOLDER"],'pubfetch',f'pubmed-{pubmed_id}.xml')

	success = download_xml(pubmed_id,filename)
	if success:
		myjson = parse_pubmed_xml(filename)
		temp_json = myjson.copy()
		article_schema = ArticleSchema()
		duplicate_count = 0
		duplicates = {"title": [], "pubmed_id": [], "doi": [], "pmc_id": []}

		publication_types = myjson.pop('publication_types')
		keywords = myjson.pop('keywords')
		authors = myjson.pop('authors')
		links = myjson.pop('links')
		# Check for duplicates
		duplicate_article = check_duplicates(myjson)
		if duplicate_article:
			duplicate_count += 1
			if duplicate_article.title is not None and duplicate_article.title == temp_json['title']:
				duplicates['title'].append({"existing": article_schema.dump(duplicate_article), "new": temp_json})
			elif duplicate_article.pubmed_id is not None and duplicate_article.pubmed_id == temp_json['pubmed_id']:
				duplicates['pubmed_id'].append({"existing": article_schema.dump(duplicate_article), "new": temp_json})
			elif duplicate_article.doi is not None and duplicate_article.doi == temp_json['doi']:
				duplicates['doi'].append({"existing": article_schema.dump(duplicate_article), "new": temp_json})
			elif duplicate_article.pmc_id is not None and duplicate_article.pmc_id == temp_json['pmc_id']:
				duplicates['pmc_id'].append({"existing": article_schema.dump(duplicate_article), "new": temp_json})

			return jsonify({
				"message": "Duplicate Article found",
				"added_articles": 0,
				"articles": article_schema.dump(duplicate_article),
				"duplicate_articles": duplicates,
			}), 400
		# Create new article
		new_article = article_schema.load(myjson)
		db.session.add(new_article)
		db.session.commit()  # Get article ID

		# Add publication types
		for pub_type in publication_types:
			pub_instance = add_or_get(PublicationType, session, publication_type=pub_type['publication_type'])
			new_article.publication_types.append(pub_instance)

		# Add keywords
		for keyword in set(kw['keyword'] for kw in keywords):  # Avoid duplicates in the same article
			keyword_instance = add_or_get(Keyword, session, keyword=keyword)
			new_article.keywords.append(keyword_instance)

		# Add links
		for link in links:
			new_link = Link(**link)
			db.session.add(new_link)
			new_article.links.append(new_link)

		# Add authors
		for idx, author in enumerate(authors):
			author_instance = add_or_get(Author, session, **author)
			new_article.authors.append(ArticleAuthor(author=author_instance, sequence_number=idx + 1))

		db.session.commit()
		app.logger.info("1 item added in the db")  
			
		return jsonify({"message": "Pubmed Article Added successfully","articles": article_schema.dump(Article.query.filter_by(id=new_article.id).first())}), 200

	else:
		return jsonify({"message":"Either you provided wrong Pubmed ID or something went wrong."}),401

@article_bp.route("/<string:id>",methods=['POST'])
@verify_USER_role
@verify_body
def updateSingle_article(data,session,id):
	article = Article.query.filter_by(uuid=id).first()
	if article and article.uuid == data['uuid']:
		
		article.title = data['title'] 
		article.abstract = data['abstract'] if 'abstract' in data else article.abstract
		article.place_of_publication = data['place_of_publication'] if 'place_of_publication' in data else article.place_of_publication
		article.journal = data['journal'] if 'journal' in data else article.journal
		article.journal_abrevated = data['journal_abrevated'] if 'journal_abrevated' in data else article.journal_abrevated
		article.publication_date = date.fromisoformat(data['publication_date']) if 'publication_date' in data else article.publication_date
		article.electronic_publication_date = date.fromisoformat(data['electronic_publication_date']) if 'electronic_publication_date' in data else article.electronic_publication_date
		article.pages = data['pages'] if 'pages' in data else article.pages
		article.journal_volume = data['journal_volume'] if 'journal_volume' in data else article.journal_volume
		article.journal_issue = data['journal_issue'] if 'journal_issue' in data else article.journal_issue

		# Identifiers
		article.pubmed_id = data['pubmed_id'] if 'pubmed_id' in data else article.pubmed_id
		article.pmc_id = data['pmc_id'] if 'pmc_id' in data else article.pmc_id
		article.pii = data['pii'] if 'pii' in data else article.pii
		article.doi = data['doi'] if 'doi' in data else article.doi
		article.print_issn = data['print_issn'] if 'print_issn' in data else article.print_issn
		article.electronic_issn = data['electronic_issn'] if 'electronic_issn' in data else article.electronic_issn
		article.linking_issn = data['linking_issn'] if 'linking_issn' in data else article.linking_issn
		article.nlm_journal_id = data['nlm_journal_id'] if 'nlm_journal_id' in data else article.nlm_journal_id


		for art_auth in ArticleAuthor.query.filter_by(article_id=article.id).all():
			db.session.delete(art_auth)
		db.session.commit()
  
		for author in data['authors']:
			if 'id' in author and author['id'] != "None-Type":
				auth_obj = Author.query.filter_by(id=author['id']).first()
				auth_obj.fullName = author['fullName'] if 'fullName' in author else auth_obj.fullName
				auth_obj.author_abbreviated = author['author_abbreviated'] if 'author_abbreviated' in author else auth_obj.author_abbreviated
				auth_obj.affiliations = author['affiliations'] if 'affiliations' in author else auth_obj.affiliations
	
				articleAuthor = ArticleAuthor(article_id=article.id,author_id=auth_obj.id)
				articleAuthor.sequence_number = author['sequence_number']
				db.session.add(articleAuthor)
	
	
			else:
				fullName = author['fullName']
				author_abbreviated = author['author_abbreviated'] if 'author_abbreviated' in author else None
				affiliations = author['affiliations'] if 'affiliations' in author else None

				auth_obj = Author(fullName=fullName,author_abbreviated=author_abbreviated,affiliations=affiliations)
				db.session.add(auth_obj)
				db.session.commit()
				articleAuthor = ArticleAuthor(article_id=article.id,author_id=auth_obj.id)
				articleAuthor.sequence_number = author['sequence_number']
				db.session.add(articleAuthor)
  
		for art_keyword in ArticleKeyword.query.filter_by(article_id=article.id).all():
			db.session.delete(art_keyword)
		db.session.commit()
  
		for keyword in data['keywords']:
			if 'id' in keyword and keyword['id'] != "None-Type":
				keyword_obj = Keyword.query.filter_by(id=keyword['id']).first()
				keyword_obj.keyword = keyword['keyword'] if 'keyword' in keyword else keyword_obj.keyword
				keywordAuthor = ArticleKeyword(article_id=article.id,keyword_id=keyword_obj.id)
				db.session.add(keywordAuthor)
			else:
				keyword_val = keyword['keyword']
				keyword_obj = Keyword(keyword = keyword_val)
				db.session.add(keyword_obj)
				db.session.commit()
				keywordAuthor = ArticleKeyword(article_id=article.id,keyword_id=keyword_obj.id)
				db.session.add(keywordAuthor)  


		for art_link in Link.query.filter_by(article_id=article.id).all():
			db.session.delete(art_link)
		db.session.commit()
  
		for link in data['links']:
			link_val = link['link']
			link_obj = Link(link = link_val,article_id=article.id)
			db.session.add(link_obj)

		db.session.commit()
		return jsonify({"message":"Updated Successfully"}),200
	else:
		return jsonify({"message":f"Article id {id} not found"}),404

def find_duplicates(model, fields,page,entry):
	"""
	Find duplicates in the database based on specified fields.

	Args:
		model: SQLAlchemy model class.
		fields: List of fields to check for duplicates (e.g., ['title', 'pmid']).

	Returns:
		dict: Dictionary where keys are fields and values are lists of duplicate groups.
	"""
		
  

	duplicates = {}
	article_schema = ArticleSchema()
	
	for field in fields:
		if db.session.query(Duplicate).filter_by(field=field).count() > 0:
			duplicate_schema = DuplicateSchema(many=True)
			field_duplicates = db.session.query(Duplicate).filter_by(field=field).all()
			duplicates[field] = duplicate_schema.dump(field_duplicates)
		else:
			# Dynamically construct the query for duplicates
			field_attr = getattr(model, field)
			duplicate_groups = (
				db.session.query(field_attr, func.group_concat(model.id).label("ids"))
				.group_by(field_attr)
				.having(func.count(field_attr) > 1)
				.all()
			)
			duplicate_schema = DuplicateSchema()
			# Parse results into groups of duplicates
			duplicate_records = []
			for _, ids in duplicate_groups:
				article_ids = list(map(int, ids.split(',')))
				value = article_schema.dump(Article.query.filter_by(id=article_ids[0]).first())[field]
				articles = []
				for row in db.session.query(Article.uuid).filter(model.id.in_(article_ids)).all():
					myuuid = row._mapping['uuid']
					# print(uuid)
					articles.append(myuuid)
				# pprint(articles)
				duplicate = Duplicate(
					uuid = str(uuid.uuid4()),
					field = field,
					value = value,
					articles = articles
				)
				db.session.add(duplicate)
				db.session.commit()
	
				duplicate_records.append(
					duplicate_schema.dump(duplicate)
				)
		
			duplicates[field] = duplicate_records

	return duplicates

@article_bp.route("/duplicates",methods=['GET'])
@verify_internal_api_id
@verify_LIBRARYMANAGER_role
def find_duplicate_groups(session):
	fields = request.args.getlist('field')
	page = request.args.get('page')
	entry = request.args.get('entry')
	if fields == []:
		fields = ['pubmed_id','doi','title','pmc_id']
	duplicates = find_duplicates(Article, fields,page,entry)

	# pprint(duplicates)
	return jsonify(duplicates),200

def calculate_font_size(article_count, min_count, max_count, min_font=10, max_font=50):
	"""
	Scale article_count to a font size between min_font and max_font.

	Args:
	- article_count (int): The count of articles.
	- min_count (int): The minimum article count in the dataset.
	- max_count (int): The maximum article count in the dataset.
	- min_font (int): Minimum font size.
	- max_font (int): Maximum font size.

	Returns:
	- int: Scaled font size.
	"""
	
	if max_count == min_count:  # Avoid division by zero
		return (max_font + min_font) // 2
	return int(((article_count - min_count) / (max_count - min_count)) * (max_font - min_font) + min_font)

# Function to check if an article matches the filter criteria
def article_matches_filter(article, filter_criteria):
	# Check if authors match
	if filter_criteria.get('authors'):
		author_names = [author['fullName'] for author in article.get('authors', [])]
		if not any(author in author_names for author in filter_criteria['authors']):
			return False

	# Check if keywords match
	if filter_criteria.get('keywords'):
		article_keywords = [keyword['keyword'] for keyword in article.get('keywords', [])]
		if any(keyword not in article_keywords for keyword in filter_criteria['keywords']):
			return False

	# Check if journal matches
	if filter_criteria.get('journals'):
		article_journal = article.get('journal', "")
		if article_journal not in filter_criteria['journals']:
			return False

	# Check if publication_date is within the date range
	start_date = filter_criteria.get('start_date')[0]
	end_date = filter_criteria.get('end_date')[0]

	if start_date or end_date:
		pub_date_str = article.get('publication_date', "")
		if pub_date_str:
			try:
				pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
			except ValueError:
				return False  # Invalid date format
		else:
			return True
		# Check against start_date if present
		if start_date and start_date!="":
			if pub_date < datetime.strptime(start_date, "%Y-%m-%d"):
				return False
		
		# Check against end_date if present
		if end_date and start_date!="":
			if pub_date > datetime.strptime(end_date, "%Y-%m-%d"):
				return False

	return True

# Function to filter articles
def filter_articles(articles, filter_criteria):
	with Pool() as pool:
		# Apply the filtering function to each article in parallel
		result = pool.starmap(article_matches_filter, [(article, filter_criteria) for article in articles])
	
	# Filter out articles where result is False (those should be removed)
	filtered_articles = [article for article, keep in zip(articles, result) if keep]
	return filtered_articles


@article_bp.route('/searchspecific', methods=['GET'])
def search_articles():
	search_params = request.args.to_dict(flat=False)  # Allows multiple values for the same key
	myquery = search_params.get('query', ["Importance of Critical View"])[0]
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 10, type=int)

	characters_to_replace = r"[!\-:&.]"
	myqueries = re.sub(characters_to_replace, " ", myquery).strip().split()

	if offset < 0 or limit <= 0:
		return jsonify({"error": "Offset must be non-negative and Limit must be greater than 0"}), 400

	server_url = get_base_url()
	url = f"{server_url}/researchrepository/api/article/search"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	search_bys = ["keyword","title","author","journal"]
	cookies = request.cookies.to_dict()  # Converts the ImmutableMultiDict to a regular dictionary

	articles_json = []
	for search_by in search_bys:
		params = {
			"q":myquery,
			"search_by":search_by,
			"offset":0,
			"limit":100000
		}
		response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

		if response.status_code==200:
			results = response.json()
			articles_json.extend(results["articles"])

	for q in myqueries:
		for search_by in search_bys:
			params = {
				"q":q,
				"search_by":search_by,
				"offset":0,
				"limit":100000
			}
			response = requests.get(url, headers=headers,params=params, cookies=cookies)  # Use `requests.get`

			if response.status_code==200:
				results = response.json()
				articles_json.extend(results["articles"])

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
  
	if articles_json == []:
		return jsonify({
			"message": "Offset exceeds the total number of results.",
			"total_articles": 0,
			"offset": offset,
			"limit": limit,
			"articles": [],
			"unique_authors": [],
			"unique_keywords": [],
			"unique_journals": [],
			"filters" : filter_json
		}), 200
  
	all_authors = {author["fullName"] for article in articles_json for author in article["authors"]}
	all_keywords = {keyword["keyword"] for article in articles_json for keyword in article["keywords"]}
	all_journals = {article["journal"] for article in articles_json}
	
	filtered_articles = filter_articles(articles_json, filter_json)

	total_articles = len(filtered_articles)
	
	# Count total articles before pagination
	if offset >= total_articles:
		print(f"{offset} - {total_articles}")
		pprint(filter_json)
		return jsonify({
			"message": "Offset exceeds the total number of results.",
			"total_articles": total_articles,
			"offset": offset,
			"limit": limit,
			"articles": [],
			"unique_authors": list(all_authors),
			"unique_keywords": list(all_keywords),
			"unique_journals": list(all_journals),
			"filters" : filter_json
		}), 200

	

	response = {
		"message": "Search successful.",
		"total_articles": total_articles,
		"offset": offset,
		"limit": limit,
		"articles": filtered_articles[offset:offset + limit],
		"unique_authors": list(all_authors),
		"unique_keywords": list(all_keywords),
		"unique_journals": list(all_journals),
		"filters" : filter_json
	}

	return jsonify(response), 200





@article_bp.route("/statistic",methods=['GET'])
def statistic():
	query = request.args.get('q','')
	if not query:
		return jsonify({"message":"Query parameter is mandatory"}),400
	
	if query == "count":
		count = Article.query.count()
		return jsonify({"message":"Successfull result","result":count}),200
	
	if query == "view":
		count = 0
		for stats in ArticleStatistic.query.all():
			count += stats.view 
		return jsonify({"message":"Successfull result","result":count}),200

	if query == "currentCount":
		current = str(datetime.now().year)
		count = 0
		results = (
				db.session.query(
					func.strftime('%Y', Article.publication_date).label('year'),  # Extract year from publication_date
					func.count(Article.id).label('count')  # Count articles
				)
				.filter(Article.publication_date.isnot(None))
				.group_by('year')  # Group by year
				.order_by('year')  # Order by year
				.all()
			)
  
		for year, mycount in results:
	  
			if year == current:
				count = mycount

		return jsonify({"message":"Successfull result","result":count}),200

	if query == "keyword":
		keyword_counts = (
			db.session.query(Keyword.keyword, func.count(ArticleKeyword.article_id).label('article_count'))
			.join(ArticleKeyword, Keyword.id == ArticleKeyword.keyword_id)
			.group_by(Keyword.id)
			.limit(200)
			.all()
		)
		min_count = min(keyword_counts, key=lambda x: x[1])[1]
		max_count = max(keyword_counts, key=lambda x: x[1])[1]
		# Format the result as a list of dictionaries
		result = [
			{"url":f"/researchrepository/keyword?q={keyword}","word": keyword, "size": calculate_font_size(article_count, min_count, max_count)}
			for keyword, article_count in keyword_counts
		]
		return jsonify({"message":"Successfull result","result":result}),200

	if query=="recentArticles":
		articles = Article.query.order_by(desc(Article.publication_date)).limit(10).all()
		article_schema = ArticleSchema(many=True)
		result = article_schema.dump(articles)
		return jsonify({"message":"Successfull result","result":result}),200
  
	if query == "yearData":    
		try:
			# Query to get counts of articles grouped by year
			results = (
				db.session.query(
					func.strftime('%Y', Article.publication_date).label('year'),  # Extract year from publication_date
					func.count(Article.id).label('count')  # Count articles
				)
				.filter(Article.publication_date.isnot(None))
				.group_by('year')  # Group by year
				.order_by('year')  # Order by year
				.all()
			)


			years = []
			values = []
			for year, count in results:
				years.append(str(year))
				values.append(count)

   
			return jsonify({"status": "success", "labels": years,"values":values}), 200

		except Exception as e:
			return jsonify({"status": "error", "message": str(e)}), 500
	
	return jsonify({"message":"Wrong parameter"}),400



def uploadDuplicate(session, request, ALLOWED_EXTENSIONS):
	if 'file' not in request.files:
		return jsonify({"error": "No file part in the request"}), 400

	file = request.files['file']

	if file.filename == '':
		return jsonify({"error": "No file selected"}), 400

	if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
		filename = file.filename
		file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

		# Save the file
		file.save(file_path)

		myjsons, skipped = fileReader(filepath=file_path)
		article_schema = ArticleSchema()
		result_ids = []
		duplicates = {"title": [], "pubmed_id": [], "doi": [], "pmc_id": []}
		duplicate_count = 0

		try:
			for myjson in myjsons:
				temp_json = myjson.copy()

				publication_types = temp_json.pop('publication_types', [])
				keywords = temp_json.pop('keywords', [])
				authors = temp_json.pop('authors', [])
				links = temp_json.pop('links', [])

				# Check for duplicates
				duplicate_article = check_duplicates(temp_json)
				if duplicate_article:
					duplicate_count += 1
					if duplicate_article.title is not None and duplicate_article.title == myjson['title']:
						duplicates['title'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
					elif duplicate_article.pubmed_id is not None and duplicate_article.pubmed_id == myjson['pubmed_id']:
						duplicates['pubmed_id'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
					elif duplicate_article.doi is not None and duplicate_article.doi == myjson['doi']:
						duplicates['doi'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
					elif duplicate_article.pmc_id is not None and duplicate_article.pmc_id == myjson['pmc_id']:
						duplicates['pmc_id'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})

 
				# Create new article
				new_article = article_schema.load(temp_json)
				db.session.add(new_article)
				db.session.commit()  # Get article ID

				# Add publication types
				for pub_type in publication_types:
					pub_instance = add_or_get(PublicationType, session, publication_type=pub_type['publication_type'])
					new_article.publication_types.append(pub_instance)

				# Add keywords
				for keyword in set(kw['keyword'] for kw in keywords):  # Avoid duplicates in the same article
					keyword_instance = add_or_get(Keyword, session, keyword=keyword)
					new_article.keywords.append(keyword_instance)

				# Add links
				for link in links:
					new_link = Link(**link)
					db.session.add(new_link)
					new_article.links.append(new_link)

				db.session.commit()
				for idx, author in enumerate(authors):
					author_instance = add_or_get(Author, session, **author)
					new_article.authors.append(ArticleAuthor(author=author_instance, sequence_number=idx + 1))

				db.session.commit()
				result_ids.append(new_article.id)

			articles = Article.query.filter(Article.id.in_(result_ids)).all()
			return jsonify({
				"message": "File uploaded successfully",
				"filename": filename,
				"added_articles": len(result_ids),
				"skipped_articles": skipped,
				"articles": ArticleSchema(many=True).dump(articles),
				"duplicate_articles": duplicates,
			}), 200

		except Exception as e:
			app.logger.error(f"Error during file processing: {str(e)}")
			traceback.print_exc()
			return jsonify({"error": "An error occurred while processing the file"}), 500

	return jsonify({"error": "Invalid file type. Only .ris files are allowed."}), 401


@article_bp.route('/authors', methods=['GET'])
@verify_session
def authors(session):
	authorSchemas = AuthorSchemaWithoutArticle(many=True)
	authors_found = Author.query.all()
	return authorSchemas.dump(authors_found),200

@article_bp.route('/keywords', methods=['GET'])
@verify_session
def keywords(session):
	keywordSchemas = KeywordSchemaWithoutArticle(many=True)
	keywords_found = Keyword.query.all()
	return keywordSchemas.dump(keywords_found),200

@article_bp.route('/journals', methods=['GET'])
@verify_session
def journals(session):
	journals_found = db.session.query(Article.journal).distinct().all()
	myjournals = [journal[0] for journal in journals_found]
	return myjournals,200


@article_bp.route('/upload_ris_duplicate', methods=['POST'])
@verify_USER_role
def upload_ris_duplicate(session):
	return uploadDuplicate(session,request,['ris'])

@article_bp.route('/upload_nbib_duplicate', methods=['POST'])
@verify_USER_role
def upload_nbib_duplicate(session):
	return uploadDuplicate(session,request,['nbib'])

@article_bp.route("/duplicate/<string:id>")
@verify_session
@verify_internal_api_id
def getSingle_duplicate(session,id):
	duplicate = Duplicate.query.filter_by(uuid=id).first()
	if duplicate:
		duplicate_schema = DuplicateSchema()
		return duplicate_schema.dump(duplicate),200
	else:
		return jsonify({"message":f"Duplicate id {id} not found"}),404



@article_bp.route("/duplicate/<string:id>/resolved",methods=["DELETE"])
@verify_session
def resolved_duplicate(session,id):
	duplicate = Duplicate.query.filter_by(uuid=id).first()
	if duplicate:
		db.session.delete(duplicate)
		db.session.commit()
		return jsonify({"message":f"Duplicate resolved : {id}"}),200
	else:
		return jsonify({"message":f"Duplicate id {id} not found"}),404





@article_bp.route("/<string:id>",methods=['DELETE'])
@verify_session
def delete_article(session,id):
	article = Article.query.filter_by(uuid=id).first()
	if article:
		article_schema = ArticleSchema()
		uuid = article.uuid
		deletedArticle = DeletedArticle(uuid = uuid,article = article_schema.dump(article))
		db.session.add(deletedArticle)
		for author in article.authors:
			db.session.delete(author)
		db.session.delete(article)

		duplicate_schema = DuplicateSchema()
		for duplicate in Duplicate.query.filter(Duplicate.articles.contains(uuid)).all():
			articles = []
			myduplicate = duplicate_schema.dump(duplicate)
			# pprint(myduplicate["articles"])
			for myuuid in myduplicate["articles"]:
				if myuuid != uuid:
					# pprint(myuuid)
					articles.append(myuuid)
			myduplicate["articles"] = articles
			# pprint(myduplicate["created_at"])
			# myduplicate["created_at"] = datetime.fromisoformat(myduplicate["created_at"])
			Duplicate.query.filter_by(id=myduplicate["id"]).delete()
			myduplicate.pop("id")
			if len(articles) > 1:
				db.session.add(duplicate_schema.load(myduplicate))
			app.logger.info(f"updating uuid {duplicate.uuid} in duplicate model")
		db.session.commit()

  
		return jsonify({"message":f"Article id {id} is deleted"}),200

	else:
		db.session.rollback()
		return jsonify({"message":f"Article id {id} not found"}),404



def search(query,author,offset,limit):    
	# Get total count of matching articles
	total_articles = query.count()

	# Handle out-of-bounds offset
	if offset >= total_articles:
		return jsonify({
			"message": "Offset exceeds the total number of results.",
			"total_articles": total_articles,
			"offset": offset,
			"limit": limit,
			"articles": []
		}),400

	# Apply offset and limit for pagination
	paginated_articles = query.offset(offset).limit(limit).all()
	article_schema = ArticleSchema(many=True)

	# Serialize the article data
	articles_data = article_schema.dump(paginated_articles)
	
	return jsonify({
		"result_for": author,
		"total_articles": total_articles,
		"offset": offset,
		"limit": limit,
		"articles": articles_data
	}),200
	

@article_bp.route("/search")
@verify_session
@verify_internal_api_id
def search_article(session):
	query = request.args.get('q','')
	search_by = request.args.get('search_by','')
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 10, type=int)
	
	if not query:
		return jsonify({"message":"Search must have a query parameter"}),401

	if offset<0 or limit <= 0:
		return jsonify({"error": "Offset must be non negative and Limit must be greater than 0"}), 400
	
	author_query = (
			db.session.query(Article)
			.join(ArticleAuthor, Article.id == ArticleAuthor.article_id)
			.join(Author, ArticleAuthor.author_id == Author.id)
			.filter(
				or_(
					Author.fullName.ilike(f"%{query}%"),  # Match full name
					Author.author_abbreviated.ilike(f"%{query}%")  # Match abbreviation
				)
			)
			.distinct()  # Ensure unique articles
		)

	keyword_query = (
			db.session.query(Article)
			.join(ArticleKeyword, Article.id == ArticleKeyword.article_id)
			.join(Keyword, ArticleKeyword.keyword_id == Keyword.id)
			.filter(Keyword.keyword.ilike(f"%{query}%"))
			.distinct()  # Ensure unique articles
		)

	journal_query = (
			db.session.query(Article)
   			.filter(
				or_(
					Article.journal.ilike(f"%{query}%"),  # Match full name
					Article.journal_abrevated.ilike(f"%{query}%")  # Match abbreviation
				)
			)
			.distinct()  # Ensure unique articles
		)

	title_query = (
			db.session.query(Article)
   			.filter(
				or_(
					Article.title.ilike(f"%{query}%"),  # Match full name
				)
			)
			.distinct()  # Ensure unique articles
		)

	if search_by == "author":
		return search(author_query,query,offset,limit)

	elif search_by == "keyword":
		return search(keyword_query,query,offset,limit)

	elif search_by == "journal":
		return search(journal_query,query,offset,limit)
	elif search_by == "title":
		return search(title_query,query,offset,limit)
	else:
		return jsonify({"message":f"Searching for {query}"}),200

