from datetime import date
import os
from pprint import pprint
import traceback
from flask import jsonify,current_app as app, request
from marshmallow import ValidationError
from sqlalchemy import or_

from sqlalchemy import func
from collections import defaultdict
from app.decorator import checkBlueprintRouteFlag, verify_LIBRARYMANAGER_role, verify_SUPERADMIN_role, verify_USER_role, verify_body, verify_internal_api_id, verify_session
from app.extension import db,scheduler
from app.models.article import Article, ArticleAuthor, ArticleKeyword, ArticlePublicationType, ArticleStatistic, Author, Duplicate, Keyword, Link, PublicationType
from app.schema import ArticleSchema, AuthorSchema, DuplicateSchema, KeywordSchema, LinkSchema, PublicationTypeSchema
from app.util import download_xml, fileReader, find_full_row_match, getUnique,  parse_pubmed_xml
from . import article_bp

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

				# Add authors
				for idx, author in enumerate(authors):
					author_instance = add_or_get(Author, session, **author)
					new_article.authors.append(ArticleAuthor(author=author_instance, sequence_number=idx + 1))

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

def find_duplicates(model, fields):
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
			
			duplicate = Duplicate(
				uuid = "",
				field = field,
				value = value,
				articles = (id for id in Article.query(Article.uuid).filter(model.id.in_(article_ids)).all())
			)
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
	if fields == []:
		fields = ['pubmed_id','doi','title','pmc_id']
	duplicates = find_duplicates(Article, fields)

	
	return jsonify(duplicates),200


@article_bp.route("/statistic",methods=['GET'])
@verify_session
def statistic(session):
		
	return jsonify({})