from datetime import date, datetime
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
from app.decorator import checkBlueprintRouteFlag, verify_FACULTY_role, verify_LIBRARYMANAGER_role, verify_SUPERADMIN_role, verify_USER_role, verify_body, verify_internal_api_id, verify_session
from app.extension import db,scheduler
from app.models.article import Article, ArticleAuthor, ArticleKeyword, ArticleStatistic, Author, DeletedArticle, Duplicate, Keyword, Link, PublicationType
from app.models.user import User
from app.schema import ArticleSchema, AuthorSchemaWithoutArticle, DuplicateSchema, KeywordSchemaWithoutArticle
from app.utility import download_xml, fileReader, get_base_url,  parse_pubmed_xml
from . import article_bp
import re
from sqlalchemy.orm import class_mapper
from sqlalchemy.exc import SQLAlchemyError
from app.mylogger import error_logger

# Logging utility
def log_error(msg):
    error_logger.error(f"[ERROR] {msg}")

def log_info(msg):
    app.logger.info(f"[INFO] {msg}")

@article_bp.route("/")
@checkBlueprintRouteFlag
@verify_SUPERADMIN_role
def index(session):
    log_info("Accessed the index route for articles.")
    return "This is the research repository article route"

@article_bp.route("/table")
@verify_session
@verify_internal_api_id
def generateTable(session):
    try:
        log_info("Generating articles table.")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("entry", 10, type=int)
        start = (page - 1) * per_page

        total = Article.query.count()
        articles = Article.query.order_by(Article.publication_date.desc()).offset(start).limit(per_page).all()
        datas = ArticleSchema(many=True).dump(articles)

        log_info(f"Successfully fetched {len(datas)} articles for page {page}.")
        return jsonify({
            "data": datas,
            "page": page,
            "total_pages": total // per_page + (1 if total % per_page > 0 else 0),
        })
    except Exception as e:
        log_error(f"Error generating articles table: {e}")
        traceback.print_exc()
        return jsonify({"error": "Failed to generate articles table"}), 500

@article_bp.route("/<string:id>")
@verify_session
@verify_internal_api_id
def getSingle_article(session, id):
    try:
        log_info(f"Fetching article with ID: {id}")
        article = Article.query.filter_by(uuid=id).first()
        if article:
            stats = ArticleStatistic.query.filter_by(article_id=article.id).first()
            if not stats:
                stats = ArticleStatistic(article_id=article.id)
                db.session.add(stats)
                db.session.commit()
            stats.viewed += 1
            db.session.commit()
            article_data = ArticleSchema().dump(article)
            log_info(f"Article with ID {id} fetched successfully.")
            return article_data, 200
        else:
            log_info(f"Article with ID {id} not found.")
            return jsonify({"message": f"Article id {id} not found"}), 404
    except Exception as e:
        log_error(f"Error fetching article with ID {id}: {e}")
        traceback.print_exc()
        return jsonify({"error": "An error occurred while fetching the article"}), 500

@article_bp.route("/ownership/<string:id>")
@verify_FACULTY_role
def getownership_article(session, id):
    try:
        log_info(f"Handling ownership for author ID: {id}")
        author = Author.query.filter_by(id=id).first()
        if author:
            if author.employee_id:
                if author.employee_id == session.user.employee_id:
                    author.employee_id = None
                    db.session.commit()
                    log_info(f"Ownership removed for author ID {id}.")
                    return jsonify({"message": "Ownership removed for the author"}), 200
                log_info(f"Ownership cannot be set for author ID {id}.")
                return jsonify({"message": "Ownership cannot be set for the author"}), 400
            author.employee_id = session.user.employee_id
            db.session.commit()
            log_info(f"Ownership set for author ID {id}.")
            return jsonify({"message": "Ownership set for the author"}), 200
        else:
            log_info(f"Author ID {id} not found.")
            return jsonify({"message": f"Author id {id} not found"}), 404
    except Exception as e:
        log_error(f"Error handling ownership for author ID {id}: {e}")
        traceback.print_exc()
        return jsonify({"error": "An error occurred while handling ownership"}), 500


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


def add_or_get(model, obj):
	"""
	Add a new record or get an existing one.
	"""
	model_class = model
	# Get all column attributes except id
	mapper = class_mapper(model_class)
	filters = [
		getattr(model_class, column.key) == getattr(obj, column.key)
		for column in mapper.columns
		if column.key not in {"id", "uuid","sequence_number"}
	]
	
	instance = model_class.query.filter(*filters).first()
	if instance:
		return instance
	instance = obj
	db.session.add(instance)
	try:
		db.session.commit()  # Assign ID without committing
	except SQLAlchemyError as e:
		db.session.rollback()
		print(f"Database query failed: {e}")
	return instance

# def upload(session, request, ALLOWED_EXTENSIONS):
#     if 'file' not in request.files:
#         log_error("No file part in the request")
#         return jsonify({"error": "No file part in the request"}), 400

#     file = request.files['file']

#     if file.filename == '':
#         log_error("No file selected")
#         return jsonify({"error": "No file selected"}), 400

#     if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
#         filename = file.filename
#         file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

#         try:
#             file.save(file_path)
#             log_info(f"File saved: {filename}")

#             myjsons, skipped = fileReader(filepath=file_path)
#             article_schema = ArticleSchema()
#             result_ids = []
#             duplicates = {"title": [], "pubmed_id": [], "doi": [], "pmc_id": []}
#             duplicate_count = 0
#             log_info(f"myjson length : {len(myjsons)}")
#             for myjson in myjsons:
#                 temp_json = myjson.copy()

#                 publication_types = temp_json.pop('publication_types', [])
#                 keywords = temp_json.pop('keywords', [])
#                 authors = temp_json.pop('authors', [])
#                 links = temp_json.pop('links', [])

#                 # Check for duplicates
#                 duplicate_article = check_duplicates(temp_json)
#                 if duplicate_article:
#                     duplicate_count += 1
#                     if duplicate_article.title is not None and duplicate_article.title == myjson['title']:
#                         duplicates['title'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
#                     elif duplicate_article.pubmed_id is not None and duplicate_article.pubmed_id == myjson['pubmed_id']:
#                         duplicates['pubmed_id'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
#                     elif duplicate_article.doi is not None and duplicate_article.doi == myjson['doi']:
#                         duplicates['doi'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})
#                     elif duplicate_article.pmc_id is not None and duplicate_article.pmc_id == myjson['pmc_id']:
#                         duplicates['pmc_id'].append({"existing": article_schema.dump(duplicate_article), "new": myjson})

#                     continue

#                 # Create new article
#                 new_article = article_schema.load(temp_json)
#                 db.session.add(new_article)
#                 db.session.commit()  # Get article ID
#                 log_info(f"Added new article: {new_article.id}")

#                 # Add publication types
#                 for pub_type in publication_types:
#                     pub_instance = add_or_get(PublicationType, PublicationType(publication_type=pub_type['publication_type']))
#                     new_article.publication_types.append(pub_instance)

#                 # Add keywords
#                 for keyword in set(kw['keyword'] for kw in keywords):  # Avoid duplicates in the same article
#                     keyword_instance = add_or_get(Keyword, Keyword(keyword=keyword))
#                     new_article.keywords.append(keyword_instance)

#                 # Add links
#                 for link in links:
#                     new_link = Link(**link)
#                     db.session.add(new_link)
#                     new_article.links.append(new_link)

#                 db.session.commit()

#                 # Add authors
#                 for idx, author in enumerate(authors):
#                     author_instance = add_or_get(Author, Author(**author))
#                     author_article_instance = add_or_get(ArticleAuthor, ArticleAuthor(article_id=new_article.id, author=author_instance, sequence_number=idx + 1))
#                     new_article.authors.append(author_article_instance)

#                 db.session.commit()

#                 result_ids.append(new_article.id)

#             articles = Article.query.filter(Article.id.in_(result_ids)).all()
#             log_info(f"Successfully added {len(result_ids)} articles")

#             return jsonify({
#                 "message": "File uploaded successfully",
#                 "filename": filename,
#                 "added_articles": len(result_ids),
#                 "skipped_articles": skipped,
#                 "articles": ArticleSchema(many=True).dump(articles),
#                 "duplicate_articles": duplicates,
#             }), 200

#         except Exception as e:
#             log_error(f"Error during file processing: {str(e)}")
#             traceback.print_exc()
#             return jsonify({"error": "An error occurred while processing the file"}), 500

#     log_error("Invalid file type. Only .ris files are allowed.")
#     return jsonify({"error": "Invalid file type. Only .ris files are allowed."}), 401

# @article_bp.route('/upload_ris', methods=['POST'])
# @verify_USER_role
# def upload_ris(session):
#     return upload(session, request, ['ris'])

# @article_bp.route('/upload_nbib', methods=['POST'])
# @verify_USER_role
# def upload_nbib(session):
#     return upload(session, request, ['nbib'])

# @article_bp.route('/pubmedFetch', methods=['POST'])
# @verify_USER_role
# @verify_body
# def pubmedFetch(data, session):
#     pubmed_id = data["pmid"]
#     filename = os.path.join(app.config["UPLOAD_FOLDER"], 'pubfetch', f'pubmed-{pubmed_id}.xml')

#     try:
#         success = download_xml(pubmed_id, filename)
#         if success:
#             myjson = parse_pubmed_xml(filename)
#             temp_json = myjson.copy()
#             article_schema = ArticleSchema()
#             duplicates = {"title": [], "pubmed_id": [], "doi": [], "pmc_id": []}

#             publication_types = myjson.pop('publication_types')
#             keywords = myjson.pop('keywords')
#             authors = myjson.pop('authors')
#             links = myjson.pop('links')

#             # Check for duplicates
#             duplicate_article = check_duplicates(myjson)
#             if duplicate_article:
#                 app.log_error("Duplicate Article found")
#                 if duplicate_article.title is not None and duplicate_article.title == temp_json['title']:
#                     duplicates['title'].append({"existing": article_schema.dump(duplicate_article), "new": temp_json})
#                 elif duplicate_article.pubmed_id is not None and duplicate_article.pubmed_id == temp_json['pubmed_id']:
#                     duplicates['pubmed_id'].append({"existing": article_schema.dump(duplicate_article), "new": temp_json})
#                 elif duplicate_article.doi is not None and duplicate_article.doi == temp_json['doi']:
#                     duplicates['doi'].append({"existing": article_schema.dump(duplicate_article), "new": temp_json})
#                 elif duplicate_article.pmc_id is not None and duplicate_article.pmc_id == temp_json['pmc_id']:
#                     duplicates['pmc_id'].append({"existing": article_schema.dump(duplicate_article), "new": temp_json})

#                 return jsonify({
#                     "message": "Duplicate Article found",
#                     "added_articles": 0,
#                     "articles": article_schema.dump(duplicate_article),
#                     "duplicate_articles": duplicates,
#                 }), 400

#             # Create new article
#             new_article = article_schema.load(myjson)
#             db.session.add(new_article)
#             db.session.commit()  # Get article ID
#             log_info(f"Added new Pubmed article: {new_article.id}")

#             # Add publication types
#             for pub_type in publication_types:
#                 pub_instance = add_or_get(PublicationType, PublicationType(publication_type=pub_type['publication_type']))
#                 new_article.publication_types.append(pub_instance)

#             # Add keywords
#             for keyword in set(kw['keyword'] for kw in keywords):
#                 keyword_instance = add_or_get(Keyword, Keyword(keyword=keyword))
#                 new_article.keywords.append(keyword_instance)

#             # Add links
#             for link in links:
#                 new_link = Link(**link)
#                 db.session.add(new_link)
#                 new_article.links.append(new_link)

#             # Add authors
#             for idx, author in enumerate(authors):
#                 author_instance = add_or_get(Author, Author(**author))
#                 new_article.authors.append(ArticleAuthor(author=author_instance, sequence_number=idx + 1))

#             db.session.commit()
#             log_info(f"Pubmed article {new_article.id} added successfully")

#             return jsonify({"message": "Pubmed Article Added successfully", "articles": article_schema.dump(Article.query.filter_by(id=new_article.id).first())}), 200
#         else:
#             log_error(f"Failed to download Pubmed article with ID {pubmed_id}")
#             return jsonify({"message": "Either you provided wrong Pubmed ID or something went wrong."}), 401
#     except Exception as e:
#         log_error(f"Error during Pubmed fetch: {str(e)}")
#         traceback.print_exc()
#         return jsonify({"error": "An error occurred while processing the Pubmed article"}), 500

# @article_bp.route("/<string:id>", methods=['POST'])
# @verify_USER_role
# @verify_body
# def updateSingle_article(data, session, id):
#     try:
#         article = Article.query.filter_by(uuid=id).first()
#         if article and article.uuid == data['uuid']:
#             log_info(f"Updating article with ID {id}")

#             # Update article fields
#             article.title = data['title']
#             article.abstract = data.get('abstract', article.abstract)
#             article.place_of_publication = data.get('place_of_publication', article.place_of_publication)
#             article.journal = data.get('journal', article.journal)
#             article.journal_abrevated = data.get('journal_abrevated', article.journal_abrevated)
#             article.publication_date = date.fromisoformat(data['publication_date']) if 'publication_date' in data else article.publication_date
#             article.electronic_publication_date = date.fromisoformat(data['electronic_publication_date']) if 'electronic_publication_date' in data else article.electronic_publication_date
#             article.pages = data.get('pages', article.pages)
#             article.journal_volume = data.get('journal_volume', article.journal_volume)
#             article.journal_issue = data.get('journal_issue', article.journal_issue)

#             # Update identifiers
#             article.pubmed_id = data.get('pubmed_id', article.pubmed_id)
#             article.pmc_id = data.get('pmc_id', article.pmc_id)
#             article.pii = data.get('pii', article.pii)
#             article.doi = data.get('doi', article.doi)
#             article.print_issn = data.get('print_issn', article.print_issn)
#             article.electronic_issn = data.get('electronic_issn', article.electronic_issn)
#             article.linking_issn = data.get('linking_issn', article.linking_issn)
#             article.nlm_journal_id = data.get('nlm_journal_id', article.nlm_journal_id)

#             # Handle authors, keywords, and links
#             for art_auth in ArticleAuthor.query.filter_by(article_id=article.id).all():
#                 db.session.delete(art_auth)
#             db.session.commit()

#             for author in data['authors']:
#                 if 'id' in author and author['id'] != "None-Type":
#                     auth_obj = Author.query.filter_by(id=author['id']).first()
#                     auth_obj.fullName = author.get('fullName', auth_obj.fullName)
#                     auth_obj.author_abbreviated = author.get('author_abbreviated', auth_obj.author_abbreviated)
#                     auth_obj.affiliations = author.get('affiliations', auth_obj.affiliations)

#                     articleAuthor = ArticleAuthor(article_id=article.id, author_id=auth_obj.id)
#                     articleAuthor.sequence_number = author['sequence_number']
#                     db.session.add(articleAuthor)
#                 else:
#                     auth_obj = Author(
#                         fullName=author['fullName'],
#                         author_abbreviated=author.get('author_abbreviated'),
#                         affiliations=author.get('affiliations')
#                     )
#                     db.session.add(auth_obj)
#                     db.session.commit()
#                     articleAuthor = ArticleAuthor(article_id=article.id, author_id=auth_obj.id)
#                     articleAuthor.sequence_number = author['sequence_number']
#                     db.session.add(articleAuthor)

#             db.session.commit()
#             log_info(f"Successfully updated article with ID {id}")
#             return jsonify({"message": "Updated Successfully"}), 200
#         else:
#             log_error(f"Article with ID {id} not found")
#             return jsonify({"message": f"Article id {id} not found"}), 404
#     except Exception as e:
#         log_error(f"Error during article update: {str(e)}")
#         traceback.print_exc()
#         return jsonify({"error": "An error occurred while updating the article"}), 500



# def find_duplicates(model, fields, page, entry):
#     """
#     Find duplicates in the database based on specified fields.
    
#     Args:
#         model: SQLAlchemy model class.
#         fields: List of fields to check for duplicates (e.g., ['title', 'pmid']).
        
#     Returns:
#         dict: Dictionary where keys are fields and values are lists of duplicate groups.
#     """
#     duplicates = {}
#     article_schema = ArticleSchema()

#     for field in fields:
#         try:
#             if db.session.query(Duplicate).filter_by(field=field).count() > 0:
#                 duplicate_schema = DuplicateSchema(many=True)
#                 field_duplicates = db.session.query(Duplicate).filter_by(field=field).all()
#                 duplicates[field] = duplicate_schema.dump(field_duplicates)
#                 log_info(f"Duplicates for field '{field}' found from Duplicate table.")
#             else:
#                 field_attr = getattr(model, field)
#                 duplicate_groups = (
#                     db.session.query(field_attr, func.group_concat(model.id).label("ids"))
#                     .group_by(field_attr)
#                     .having(func.count(field_attr) > 1)
#                     .all()
#                 )
#                 duplicate_schema = DuplicateSchema()
#                 duplicate_records = []
#                 for _, ids in duplicate_groups:
#                     article_ids = list(map(int, ids.split(',')))
#                     value = article_schema.dump(Article.query.filter_by(id=article_ids[0]).first())[field]
#                     articles = [row._mapping['uuid'] for row in db.session.query(Article.uuid).filter(model.id.in_(article_ids)).all()]
                    
#                     duplicate = Duplicate(
#                         uuid=str(uuid.uuid4()),
#                         field=field,
#                         value=value,
#                         articles=articles
#                     )
                    
#                     db.session.add(duplicate)
#                     db.session.commit()  # Commit inside the loop to ensure that each duplicate is saved
#                     duplicate_records.append(duplicate_schema.dump(duplicate))
#                 duplicates[field] = duplicate_records
#                 log_info(f"Duplicates for field '{field}' added to Duplicate table.")
#         except Exception as e:
#             log_error(f"Error while processing duplicates for field '{field}': {str(e)}")
#             db.session.rollback()  # Rollback in case of error
#     return duplicates

# @article_bp.route("/duplicates", methods=['GET'])
# @verify_internal_api_id
# @verify_LIBRARYMANAGER_role
# def find_duplicate_groups(session):
#     fields = request.args.getlist('field')
#     page = request.args.get('page')
#     entry = request.args.get('entry')
#     if not fields:
#         fields = ['pubmed_id', 'doi', 'title', 'pmc_id']
    
#     try:
#         duplicates = find_duplicates(Article, fields, page, entry)
#         log_info(f"Duplicate groups found: {duplicates}")
#         return jsonify(duplicates), 200
#     except Exception as e:
#         log_error(f"Error in finding duplicate groups: {str(e)}")
#         return jsonify({"error": "An error occurred while processing your request."}), 500

# def calculate_font_size(article_count, min_count, max_count, min_font=10, max_font=50):
#     """
#     Scale article_count to a font size between min_font and max_font.
    
#     Args:
#         article_count (int): The count of articles.
#         min_count (int): The minimum article count in the dataset.
#         max_count (int): The maximum article count in the dataset.
#         min_font (int): Minimum font size.
#         max_font (int): Maximum font size.
    
#     Returns:
#         int: Scaled font size.
#     """
#     if max_count == min_count:  # Avoid division by zero
#         return (max_font + min_font) // 2
#     return int(((article_count - min_count) / (max_count - min_count)) * (max_font - min_font) + min_font)

# def article_matches_filter(article, filter_criteria):
#     # Check if authors match
#     if filter_criteria.get('authors'):
#         author_names = [author['fullName'] for author in article.get('authors', [])]
#         if not any(author in author_names for author in filter_criteria['authors']):
#             return False

#     # Check if keywords match
#     if filter_criteria.get('keywords'):
#         article_keywords = [keyword['keyword'] for keyword in article.get('keywords', [])]
#         if any(keyword not in article_keywords for keyword in filter_criteria['keywords']):
#             return False

#     # Check if journal matches
#     if filter_criteria.get('journals'):
#         article_journal = article.get('journal', "")
#         if article_journal not in filter_criteria['journals']:
#             return False

#     # Check if publication_date is within the date range
#     start_date = filter_criteria.get('start_date')[0] if isinstance(filter_criteria.get('start_date'), list) else filter_criteria.get('start_date')
#     end_date = filter_criteria.get('end_date')[0] if isinstance(filter_criteria.get('end_date'), list) else filter_criteria.get('end_date')

#     if start_date or end_date:
#         pub_date_str = article.get('publication_date', "")
#         if pub_date_str:
#             try:
#                 pub_date = datetime.strptime(pub_date_str, "%Y-%m-%d")
#             except ValueError:
#                 return False  # Invalid date format
#         else:
#             return True

#         if start_date and start_date != "" and pub_date < datetime.strptime(start_date, "%Y-%m-%d"):
#             return False
#         if end_date and end_date != "" and pub_date > datetime.strptime(end_date, "%Y-%m-%d"):
#             return False

#     return True

# def filter_articles(articles, filter_criteria):
#     with Pool() as pool:
#         result = pool.starmap(article_matches_filter, [(article, filter_criteria) for article in articles])
#     return [article for article, keep in zip(articles, result) if keep]

# @article_bp.route('/searchspecific', methods=['GET'])
# def search_articles():
#     search_params = request.args.to_dict(flat=False)
#     myquery = search_params.get('query', [""])[0]
#     offset = request.args.get('offset', 0, type=int)
#     limit = request.args.get('limit', 10, type=int)

#     characters_to_replace = r"[!\-:&.]"
#     myqueries = re.sub(characters_to_replace, " ", myquery).strip().split()

#     if offset < 0 or limit <= 0:
#         return jsonify({"error": "Offset must be non-negative and Limit must be greater than 0"}), 400

#     server_url = get_base_url()
#     url = f"{server_url}/api/article/search"
#     headers = {"API-ID": app.config.get('API_ID')}
#     cookies = request.cookies.to_dict()

#     articles_json = []
#     for search_by in ["keyword", "title", "author", "journal", "pubmed_id", "doi"]:
#         params = {
#             "q": myquery,
#             "search_by": search_by,
#             "offset": 0,
#             "limit": 100000
#         }
#         try:
#             response = requests.get(url, headers=headers, params=params, cookies=cookies)
#             if response.status_code == 200:
#                 results = response.json()
#                 articles_json.extend(results["articles"])
#             else:
#                 log_error(f"Failed request with status code {response.status_code} for search_by {search_by}")
#         except Exception as e:
#             log_error(f"Error during search request: {str(e)}")

#     for q in myqueries:
#         for search_by in ["keyword", "title", "author", "journal", "pubmed_id", "doi"]:
#             params = {
#                 "q": q,
#                 "search_by": search_by,
#                 "offset": 0,
#                 "limit": 100000
#             }
#             try:
#                 response = requests.get(url, headers=headers, params=params, cookies=cookies)
#                 if response.status_code == 200:
#                     results = response.json()
#                     articles_json.extend(results["articles"])
#                 else:
#                     log_error(f"Failed request with status code {response.status_code} for search_by {search_by}")
#             except Exception as e:
#                 log_error(f"Error during search request: {str(e)}")

#     articles_json = {v['uuid']: v for v in articles_json}.values()

#     # Apply filters
#     filter_json = {}
#     for key in ['authors', 'keywords', 'start_date', 'end_date', 'journals']:
#         if key in search_params:
#             filter_json[key] = search_params[key]

#     if not articles_json:
#         return jsonify({
#             "message": "Offset exceeds the total number of results.",
#             "total_articles": 0,
#             "offset": offset,
#             "limit": limit,
#             "articles": [],
#             "unique_authors": [],
#             "unique_keywords": [],
#             "unique_journals": [],
#             "filters": filter_json
#         }), 200

#     all_authors = {author["fullName"] for article in articles_json for author in article["authors"]}
#     all_keywords = {keyword["keyword"] for article in articles_json for keyword in article["keywords"]}
#     all_journals = {article["journal"] for article in articles_json}

#     filtered_articles = filter_articles(articles_json, filter_json)

#     total_articles = len(filtered_articles)

#     if offset >= total_articles:
#         return jsonify({
#             "message": "Offset exceeds the total number of results.",
#             "total_articles": total_articles,
#             "offset": offset,
#             "limit": limit,
#             "articles": [],
#             "unique_authors": list(all_authors),
#             "unique_keywords": list(all_keywords),
#             "unique_journals": list(all_journals),
#             "filters": filter_json
#         }), 200

#     response = {
#         "message": "Search successful.",
#         "total_articles": total_articles,
#         "offset": offset,
#         "limit": limit,
#         "articles": filtered_articles[offset:offset + limit],
#         "unique_authors": list(all_authors),
#         "unique_keywords": list(all_keywords),
#         "unique_journals": list(all_journals),
#         "filters": filter_json
#     }

#     return jsonify(response), 200


# def find_duplicates(model, fields, page, entry):
#     """
#     Find duplicates in the database based on specified fields.

#     Args:
#         model: SQLAlchemy model class.
#         fields: List of fields to check for duplicates (e.g., ['title', 'pmid']).

#     Returns:
#         dict: Dictionary where keys are fields and values are lists of duplicate groups.
#     """
#     try:
#         duplicates = {}
#         article_schema = ArticleSchema()
        
#         for field in fields:
#             if db.session.query(Duplicate).filter_by(field=field).count() > 0:
#                 duplicate_schema = DuplicateSchema(many=True)
#                 field_duplicates = db.session.query(Duplicate).filter_by(field=field).all()
#                 duplicates[field] = duplicate_schema.dump(field_duplicates)
#             else:
#                 field_attr = getattr(model, field)
#                 duplicate_groups = (
#                     db.session.query(field_attr, func.group_concat(model.id).label("ids"))
#                     .group_by(field_attr)
#                     .having(func.count(field_attr) > 1)
#                     .all()
#                 )
#                 duplicate_schema = DuplicateSchema()
#                 duplicate_records = []
#                 for _, ids in duplicate_groups:
#                     article_ids = list(map(int, ids.split(',')))
#                     value = article_schema.dump(Article.query.filter_by(id=article_ids[0]).first())[field]
#                     articles = []
#                     for row in db.session.query(Article.uuid).filter(model.id.in_(article_ids)).all():
#                         myuuid = row._mapping['uuid']
#                         articles.append(myuuid)
#                     duplicate = Duplicate(
#                         uuid=str(uuid.uuid4()),
#                         field=field,
#                         value=value,
#                         articles=articles
#                     )
#                     db.session.add(duplicate)
#                     db.session.commit()

#                     duplicate_records.append(
#                         duplicate_schema.dump(duplicate)
#                     )

#                 duplicates[field] = duplicate_records
        
#         return duplicates
#     except Exception as e:
#         log_error(f"Error in find_duplicates: {str(e)}")
#         db.session.rollback()
#         raise

# @article_bp.route("/statistic", methods=['GET'])
# def statistic():
#     try:
#         query = request.args.get('q', '')
#         if not query:
#             log_error("Query parameter 'q' is missing")
#             return jsonify({"message": "Query parameter is mandatory"}), 400

#         if query == "count":
#             count = Article.query.count()
#             return jsonify({"message": "Successful result", "result": count}), 200

#         if query == "view":
#             count = sum(stats.viewed for stats in ArticleStatistic.query.all())
#             return jsonify({"message": "Successful result", "result": count}), 200

#         if query == "currentCount":
#             current = str(datetime.now().year)
#             count = 0
#             results = (
#                 db.session.query(
#                     func.strftime('%Y', Article.publication_date).label('year'),
#                     func.count(Article.id).label('count')
#                 )
#                 .filter(Article.publication_date.isnot(None))
#                 .group_by('year')
#                 .order_by('year')
#                 .all()
#             )

#             for year, mycount in results:
#                 if year == current:
#                     count = mycount

#             return jsonify({"message": "Successful result", "result": count}), 200

#         if query == "keyword":
#             keyword_counts = (
#                 db.session.query(Keyword.keyword, func.count(ArticleKeyword.article_id).label('article_count'))
#                 .join(ArticleKeyword, Keyword.id == ArticleKeyword.keyword_id)
#                 .group_by(Keyword.id)
#                 .limit(200)
#                 .all()
#             )
#             if keyword_counts:
#                 min_count = min(keyword_counts, key=lambda x: x[1])[1]
#                 max_count = max(keyword_counts, key=lambda x: x[1])[1]
#             else:
#                 min_count = 0
#                 max_count = 0
#             result = [
#                 {"url": f"/keyword?q={keyword}", "word": keyword, "size": calculate_font_size(article_count, min_count, max_count)}
#                 for keyword, article_count in keyword_counts
#             ]
#             return jsonify({"message": "Successful result", "result": result}), 200

#         if query == "recentArticles":
#             articles = Article.query.order_by(desc(Article.publication_date)).limit(10).all()
#             article_schema = ArticleSchema(many=True)
#             result = article_schema.dump(articles)
#             return jsonify({"message": "Successful result", "result": result}), 200

#         if query == "yearData":
#             try:
#                 results = (
#                     db.session.query(
#                         func.strftime('%Y', Article.publication_date).label('year'),
#                         func.count(Article.id).label('count')
#                     )
#                     .filter(Article.publication_date.isnot(None))
#                     .group_by('year')
#                     .order_by('year')
#                     .all()
#                 )

#                 years = []
#                 values = []
#                 for year, count in results:
#                     years.append(str(year))
#                     values.append(count)

#                 return jsonify({"status": "success", "labels": years, "values": values}), 200

#             except Exception as e:
#                 log_error(f"Error in yearData query: {str(e)}")
#                 return jsonify({"status": "error", "message": str(e)}), 500

#         return jsonify({"message": "Wrong parameter"}), 400
#     except Exception as e:
#         log_error(f"Error in statistic endpoint: {str(e)}")
#         return jsonify({"message": "Internal server error"}), 500

# @article_bp.route('/authors', methods=['GET'])
# @verify_session
# def authors(session):
#     try:
#         authorSchemas = AuthorSchemaWithoutArticle(many=True)
#         authors_found = Author.query.all()
#         log_info(f"Fetched {len(authors_found)} authors")
#         return authorSchemas.dump(authors_found), 200
#     except Exception as e:
#         log_error(f"Error fetching authors: {str(e)}")
#         return jsonify({"message": "Internal server error"}), 500

# @article_bp.route('/keywords', methods=['GET'])
# @verify_session
# def keywords(session):
#     try:
#         keywordSchemas = KeywordSchemaWithoutArticle(many=True)
#         keywords_found = Keyword.query.all()
#         log_info(f"Fetched {len(keywords_found)} keywords")
#         return keywordSchemas.dump(keywords_found), 200
#     except Exception as e:
#         log_error(f"Error fetching keywords: {str(e)}")
#         return jsonify({"message": "Internal server error"}), 500

# @article_bp.route('/journals', methods=['GET'])
# @verify_session
# def journals(session):
#     try:
#         journals_found = db.session.query(Article.journal).distinct().all()
#         myjournals = [journal[0] for journal in journals_found]
#         log_info(f"Fetched {len(myjournals)} distinct journals")
#         return myjournals, 200
#     except Exception as e:
#         log_error(f"Error fetching journals: {str(e)}")
#         return jsonify({"message": "Internal server error"}), 500

# @article_bp.route("/duplicate/<string:id>")
# @verify_session
# @verify_internal_api_id
# def getSingle_duplicate(session, id):
#     try:
#         duplicate = Duplicate.query.filter_by(uuid=id).first()
#         if duplicate:
#             duplicate_schema = DuplicateSchema()
#             return duplicate_schema.dump(duplicate), 200
#         else:
#             log_error(f"Duplicate id {id} not found")
#             return jsonify({"message": f"Duplicate id {id} not found"}), 404
#     except Exception as e:
#         log_error(f"Error fetching duplicate {id}: {str(e)}")
#         return jsonify({"message": "Internal server error"}), 500

# @article_bp.route("/duplicate/<string:id>/resolved", methods=["DELETE"])
# @verify_session
# def resolved_duplicate(session, id):
#     try:
#         duplicate = Duplicate.query.filter_by(uuid=id).first()
#         if duplicate:
#             db.session.delete(duplicate)
#             db.session.commit()
#             log_info(f"Duplicate {id} resolved and deleted")
#             return jsonify({"message": f"Duplicate resolved: {id}"}), 200
#         else:
#             log_error(f"Duplicate id {id} not found")
#             return jsonify({"message": f"Duplicate id {id} not found"}), 404
#     except Exception as e:
#         log_error(f"Error resolving duplicate {id}: {str(e)}")
#         db.session.rollback()
#         return jsonify({"message": "Internal server error"}), 500

# @article_bp.route("/<string:id>", methods=['DELETE'])
# @verify_session
# def delete_article(session, id):
#     try:
#         article = Article.query.filter_by(uuid=id).first()
#         if article:
#             article_schema = ArticleSchema()
#             uuid = article.uuid
#             deletedArticle = DeletedArticle(uuid=uuid, article=article_schema.dump(article))
#             db.session.add(deletedArticle)
#             for author in article.authors:
#                 db.session.delete(author)
#             db.session.delete(article)

#             duplicate_schema = DuplicateSchema()
#             for duplicate in Duplicate.query.filter(Duplicate.articles.contains(uuid)).all():
#                 articles = []
#                 myduplicate = duplicate_schema.dump(duplicate)
#                 for myuuid in myduplicate["articles"]:
#                     if myuuid != uuid:
#                         articles.append(myuuid)
#                 myduplicate["articles"] = articles
#                 Duplicate.query.filter_by(id=myduplicate["id"]).delete()
#                 myduplicate.pop("id")
#                 if len(articles) > 1:
#                     db.session.add(duplicate_schema.load(myduplicate))
#                 log_info(f"Updating uuid {duplicate.uuid} in duplicate model")

#             db.session.commit()
#             log_info(f"Article id {id} deleted successfully")
#             return jsonify({"message": f"Article id {id} is deleted"}), 200
#         else:
#             db.session.rollback()
#             log_error(f"Article id {id} not found")
#             return jsonify({"message": f"Article id {id} not found"}), 404
#     except Exception as e:
#         log_error(f"Error deleting article {id}: {str(e)}")
#         db.session.rollback()
#         return jsonify({"message": "Internal server error"}), 500


# def search(query, author, offset, limit, result_for=None):
#     try:
#         # Get total count of matching articles
#         total_articles = query.count()

#         # Handle out-of-bounds offset
#         if offset >= total_articles:
#             log_error(f"Offset exceeds total articles. Offset: {offset}, Total: {total_articles}")
#             return jsonify({
#                 "result_for": result_for if result_for else author,
#                 "message": "Offset exceeds the total number of results.",
#                 "total_articles": total_articles,
#                 "offset": offset,
#                 "limit": limit,
#                 "articles": []
#             }), 200

#         # Apply offset and limit for pagination
#         paginated_articles = query.offset(offset).limit(limit).all()
#         article_schema = ArticleSchema(many=True)

#         # Serialize the article data
#         articles_data = article_schema.dump(paginated_articles)

#         log_info(f"Returning {len(articles_data)} articles for query: {author} (Result For: {result_for})")
#         return jsonify({
#             "result_for": result_for if result_for else author,
#             "total_articles": total_articles,
#             "offset": offset,
#             "limit": limit,
#             "articles": articles_data
#         }), 200
#     except Exception as e:
#         log_error(f"Error in search function: {str(e)}")
#         return jsonify({"message": "Internal server error"}), 500

# @article_bp.route("/search")
# @verify_session
# @verify_internal_api_id
# def search_article(session):
#     try:
#         query = request.args.get('q', '')
#         search_by = request.args.get('search_by', '')
#         offset = request.args.get('offset', 0, type=int)
#         limit = request.args.get('limit', 10, type=int)
        
#         if not query:
#             log_error("Search must have a query parameter")
#             return jsonify({"message": "Search must have a query parameter"}), 401

#         if offset < 0 or limit <= 0:
#             log_error(f"Invalid offset or limit. Offset: {offset}, Limit: {limit}")
#             return jsonify({"error": "Offset must be non-negative and Limit must be greater than 0"}), 400

#         # Define search queries
#         author_query = (
#             db.session.query(Article)
#             .join(ArticleAuthor, Article.id == ArticleAuthor.article_id)
#             .join(Author, ArticleAuthor.author_id == Author.id)
#             .filter(
#                 or_(
#                     Author.fullName.ilike(f"%{query}%"),
#                     Author.author_abbreviated.ilike(f"%{query}%")
#                 )
#             )
#             .distinct()
#         )
#         employee_query = (
#             db.session.query(Article)
#             .join(ArticleAuthor, Article.id == ArticleAuthor.article_id)
#             .join(Author, ArticleAuthor.author_id == Author.id)
#             .filter(
#                 or_(
#                     Author.employee_id.ilike(f"%{query}%"),
#                     Author.author_abbreviated.ilike(f"%{query}%")
#                 )
#             )
#             .distinct()
#         )
#         keyword_query = (
#             db.session.query(Article)
#             .join(ArticleKeyword, Article.id == ArticleKeyword.article_id)
#             .join(Keyword, ArticleKeyword.keyword_id == Keyword.id)
#             .filter(Keyword.keyword.ilike(f"%{query}%"))
#             .distinct()
#         )
#         journal_query = (
#             db.session.query(Article)
#             .filter(
#                 or_(
#                     Article.journal.ilike(f"%{query}%"),
#                     Article.journal_abrevated.ilike(f"%{query}%")
#                 )
#             )
#             .distinct()
#         )
#         title_query = (
#             db.session.query(Article)
#             .filter(Article.title.ilike(f"%{query}%"))
#             .distinct()
#         )
#         pubmed_query = (
#             db.session.query(Article)
#             .filter(Article.pubmed_id.ilike(f"%{query}%"))
#             .distinct()
#         )
#         doi_query = (
#             db.session.query(Article)
#             .filter(Article.doi.ilike(f"%{query}%"))
#             .distinct()
#         )

#         # Handle different search types
#         if search_by == "author":
#             return search(author_query, query, offset, limit)

#         elif search_by == "keyword":
#             return search(keyword_query, query, offset, limit)

#         elif search_by == "journal":
#             return search(journal_query, query, offset, limit)

#         elif search_by == "title":
#             return search(title_query, query, offset, limit)

#         elif search_by == "pubmed_id":
#             return search(pubmed_query, query, offset, limit)

#         elif search_by == "doi":
#             return search(doi_query, query, offset, limit)

#         elif search_by == "employee":
#             user = User.query.filter_by(employee_id=query).first()
#             if user:
#                 return search(employee_query, query, offset, limit, result_for=f"{user.firstname} {user.lastname}")
#             else:
#                 log_error(f"Wrong employee ID: {query}")
#                 return jsonify({"message": f"Wrong employee ID: {query}"}), 400

#         else:
#             return jsonify({"message": f"Searching for {query}"}), 200

#     except Exception as e:
#         log_error(f"Error in search_article endpoint: {str(e)}")
#         return jsonify({"message": "Internal server error"}), 500
    
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
		app.logger.info(f"File saved at {file_path}")

		myjsons, skipped = fileReader(filepath=file_path)
		article_schema = ArticleSchema()
		result_ids = []
		duplicates = {"title": [], "pubmed_id": [], "doi": [], "pmc_id": []}
		duplicate_count = 0

		try:
			app.logger.info(f"length of myjsons:{myjsons}")
			for myjson in myjsons:
				temp_json = myjson.copy()
				app.logger.info(f"current json : {temp_json}")

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
					app.logger.info(f"skipping here")

					continue
 
				# Create new article
				new_article = article_schema.load(temp_json)
				db.session.add(new_article)
				db.session.commit()  # Get article ID

				# Add publication types
				for pub_type in publication_types:
					pub_instance = add_or_get(PublicationType, PublicationType(publication_type=pub_type['publication_type']))
					new_article.publication_types.append(pub_instance)

				# Add keywords
				for keyword in set(kw['keyword'] for kw in keywords):  # Avoid duplicates in the same article
					keyword_instance = add_or_get(Keyword, Keyword(keyword=keyword))
					new_article.keywords.append(keyword_instance)

				# Add links
				for link in links:
					new_link = Link(**link)
					db.session.add(new_link)
					new_article.links.append(new_link)

				db.session.commit()
				for idx, author in enumerate(authors):
					author_instance = add_or_get(Author, Author(**author))
					author_article_instance = add_or_get(ArticleAuthor,ArticleAuthor(article_id = new_article.id,author=author_instance, sequence_number=idx + 1))
					
					new_article.authors.append(author_article_instance)

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
			log_error(f"Error during file processing: {str(e)}")
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
			pub_instance = add_or_get(PublicationType, PublicationType( publication_type=pub_type['publication_type']))
			new_article.publication_types.append(pub_instance)

		# Add keywords
		for keyword in set(kw['keyword'] for kw in keywords):  # Avoid duplicates in the same article
			keyword_instance = add_or_get(Keyword, Keyword(keyword=keyword))
			new_article.keywords.append(keyword_instance)

		# Add links
		for link in links:
			new_link = Link(**link)
			db.session.add(new_link)
			new_article.links.append(new_link)

		# Add authors
		for idx, author in enumerate(authors):
			author_instance = add_or_get(Author, Author( **author))
			new_article.authors.append(ArticleAuthor(author=author_instance, sequence_number=idx + 1))

		db.session.commit()
		log_info("1 item added in the db")  
			
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
	start_date = filter_criteria.get('start_date')[0] if type(filter_criteria.get('start_date')) == list else filter_criteria.get('start_date')
	end_date = filter_criteria.get('end_date')[0] if type(filter_criteria.get('end_date')) == list else filter_criteria.get('end_date')

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
	myquery = search_params.get('query', [""])[0]
	offset = request.args.get('offset', 0, type=int)
	limit = request.args.get('limit', 10, type=int)

	characters_to_replace = r"[!\-:&.]"
	myqueries = re.sub(characters_to_replace, " ", myquery).strip().split()

	if offset < 0 or limit <= 0:
		return jsonify({"error": "Offset must be non-negative and Limit must be greater than 0"}), 400

	server_url = get_base_url()
	url = f"{server_url}/api/article/search"
	headers = {
		"API-ID":app.config.get('API_ID')
	}

	search_bys = ["keyword","title","author","journal","pubmed_id","doi"]
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

	articles_json =  {v['uuid']:v for v in articles_json}.values()

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
			count += stats.viewed 
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
		if keyword_counts:
			min_count = min(keyword_counts, key=lambda x: x[1])[1]
			max_count = max(keyword_counts, key=lambda x: x[1])[1]
		else:
			min_count = 0
			max_count = 0
		# Format the result as a list of dictionaries
		result = [
			{"url":f"/keyword?q={keyword}","word": keyword, "size": calculate_font_size(article_count, min_count, max_count)}
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


@article_bp.route("/duplicate/<string:id>")
@verify_LIBRARYMANAGER_role
@verify_internal_api_id
def getSingle_duplicate(session,id):
	duplicate = Duplicate.query.filter_by(uuid=id).first()
	if duplicate:
		duplicate_schema = DuplicateSchema()
		return duplicate_schema.dump(duplicate),200
	else:
		return jsonify({"message":f"Duplicate id {id} not found"}),404


@article_bp.route("/duplicate/<string:id>/resolved",methods=["DELETE"])
@verify_LIBRARYMANAGER_role
def resolved_duplicate(session,id):
	duplicate = Duplicate.query.filter_by(uuid=id).first()
	if duplicate:
		db.session.delete(duplicate)
		db.session.commit()
		return jsonify({"message":f"Duplicate resolved : {id}"}),200
	else:
		return jsonify({"message":f"Duplicate id {id} not found"}),404


@article_bp.route("/<string:id>",methods=['DELETE'])
@verify_LIBRARYMANAGER_role
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
			log_info(f"updating uuid {duplicate.uuid} in duplicate model")
		db.session.commit()

  
		return jsonify({"message":f"Article id {id} is deleted"}),200

	else:
		db.session.rollback()
		return jsonify({"message":f"Article id {id} not found"}),404


def search(query,author,offset,limit,result_for=None):    
	# Get total count of matching articles
	total_articles = query.count()

	# Handle out-of-bounds offset
	if offset >= total_articles:
		return jsonify({
			"result_for": result_for if result_for else author,
			"message": "Offset exceeds the total number of results.",
			"total_articles": total_articles,
			"offset": offset,
			"limit": limit,
			"articles": []
		}),200

	# Apply offset and limit for pagination
	paginated_articles = query.offset(offset).limit(limit).all()
	article_schema = ArticleSchema(many=True)

	# Serialize the article data
	articles_data = article_schema.dump(paginated_articles)
	
	return jsonify({
		"result_for": result_for if result_for else author,
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
	employee_query = (
			db.session.query(Article)
			.join(ArticleAuthor, Article.id == ArticleAuthor.article_id)
			.join(Author, ArticleAuthor.author_id == Author.id)
			.filter(
				or_(
					Author.employee_id.ilike(f"%{query}%"),  # Match full name
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


	pubmed_query = (
			db.session.query(Article)
   			.filter(
				or_(
					Article.pubmed_id.ilike(f"%{query}%"),  # Match full name
				)
			)
			.distinct()  # Ensure unique articles
		)

	doi_query = (
			db.session.query(Article)
   			.filter(
				or_(
					Article.doi.ilike(f"%{query}%"),  # Match full name
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

	elif search_by == "pubmed_id":
		return search(pubmed_query,query,offset,limit)

	elif search_by == "doi":
		return search(doi_query,query,offset,limit)

	elif search_by =="employee":
		user = User.query.filter_by(employee_id=query).first()
		if user:
			return search(employee_query,query,offset,limit,result_for=f"{user.firstname} {user.lastname}")
		else:
			return jsonify({"message":f"Wrong employee ID :  {query}"}),400

	else:
		return jsonify({"message":f"Searching for {query}"}),200

