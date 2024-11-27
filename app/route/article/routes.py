from datetime import date
import os
from pprint import pprint
from flask import jsonify,current_app as app, request
from marshmallow import ValidationError

from sqlalchemy import func
from collections import defaultdict
from app.decorator import checkBlueprintRouteFlag, verify_LIBRARYMANAGER_role, verify_SUPERADMIN_role, verify_USER_role, verify_body, verify_internal_api_id, verify_session
from app.extension import db,scheduler
from app.models.article import Article, ArticleAuthor, ArticleKeyword, ArticlePublicationType, Author, Keyword, Link, PublicationType
from app.schema import ArticleSchema, AuthorSchema, KeywordSchema, LinkSchema, PublicationTypeSchema
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
		
		return article_schema.dump(article)
	else:
		return jsonify({"message":f"Article id {id} not found"}),404

def upload(session, request, ALLOWED_EXTENSIONS):
	# Check if the file part is present in the request
	if 'file' not in request.files:
		return jsonify({"error": "No file part in the request"}), 400

	file = request.files['file']

	# Check if a file was submitted
	if file.filename == '':
		return jsonify({"error": "No file selected"}), 400

	# Check if the file is allowed
	if file and '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
		filename = file.filename
		file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
		
		# Save the file
		file.save(file_path)
		
		myjsons = fileReader(filepath=file_path)
		articleSchema = ArticleSchema()
		authorSchema = AuthorSchema()
		keywordSchema = KeywordSchema()
		linkSchema = LinkSchema()
		publicationTypeSchema = PublicationTypeSchema()
		
		try:
			for myjson in myjsons:
				publication_types = myjson.pop('publication_types')
				keywords = myjson.pop('keywords')
				authors = myjson.pop('authors')
				links = myjson.pop('links')

				newArticle = articleSchema.load(myjson)
				db.session.add(newArticle)

				for pub_type in publication_types:
					new_pub_type = publicationTypeSchema.load(pub_type)
	
					old_pub_type = PublicationType.query.filter_by(
						publication_type = new_pub_type.publication_type
					).first()
					if old_pub_type:
						new_article_pub_type = ArticlePublicationType(article_id=newArticle.id, publication_type_id=old_pub_type.id)
					else:
						db.session.add(new_pub_type)
						db.session.commit()
						new_article_pub_type = ArticlePublicationType(article_id=newArticle.id, publication_type_id=new_pub_type.id)
					db.session.add(new_article_pub_type)

				for keyword in getUnique(keywords):
					new_keyword = keywordSchema.load(keyword)
	
					old_keyword = Keyword.query.filter_by(
						keyword = new_keyword.keyword
					).first()
					if old_keyword:
						new_article_keyword = ArticleKeyword(article_id=newArticle.id, keyword_id=old_keyword.id)
					else:
						db.session.add(new_keyword)
						db.session.commit()
						new_article_keyword = ArticleKeyword(article_id=newArticle.id, keyword_id=new_keyword.id)
					db.session.add(new_article_keyword)

				for link in links:
					newArticle.links.append(linkSchema.load(link))

				for idx, author in enumerate(authors):
					new_author = authorSchema.load(author)
					db.session.add(new_author)
					db.session.commit()
					new_article_author = ArticleAuthor(article_id=newArticle.id, author_id=new_author.id, sequence_number=idx+1)
					db.session.add(new_article_author)


			db.session.commit()

			app.logger.info(f"{len(myjsons)} added in the db")

			return jsonify({"message": "File uploaded successfully", "filename": filename, "length": len(myjsons)}), 200

		except Exception as e:
			db.session.rollback()
			app.logger.error(f"Error during file processing: {str(e)}")
			return jsonify({"error": "An error occurred while processing the file"}), 500

	else:
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
		articleSchema = ArticleSchema()
		authorSchema = AuthorSchema()
		keywordSchema = KeywordSchema()
		linkSchema = LinkSchema()
		publicationTypeSchema = PublicationTypeSchema()

		publication_types = myjson.pop('publication_types')
		keywords = myjson.pop('keywords')
		authors = myjson.pop('authors')
		links = myjson.pop('links')
		newArticle = articleSchema.load(myjson)
		db.session.add(newArticle)

		for pub_type in publication_types:
			new_pub_type = publicationTypeSchema.load(pub_type)

			old_pub_type = PublicationType.query.filter_by(
				publication_type = new_pub_type.publication_type
			).first()
			if old_pub_type:
				new_article_pub_type = ArticlePublicationType(article_id=newArticle.id, publication_type_id=old_pub_type.id)
			else:
				db.session.add(new_pub_type)
				db.session.commit()
				new_article_pub_type = ArticlePublicationType(article_id=newArticle.id, publication_type_id=new_pub_type.id)
			db.session.add(new_article_pub_type)

		for keyword in getUnique(keywords):
			new_keyword = keywordSchema.load(keyword)

			old_keyword = Keyword.query.filter_by(
				keyword = new_keyword.keyword
			).first()
			if old_keyword:
				new_article_keyword = ArticleKeyword(article_id=newArticle.id, keyword_id=old_keyword.id)
			else:
				db.session.add(new_keyword)
				db.session.commit()
				new_article_keyword = ArticleKeyword(article_id=newArticle.id, keyword_id=new_keyword.id)
			db.session.add(new_article_keyword)

		for link in links:
			newArticle.links.append(linkSchema.load(link))


		for idx, author in enumerate(authors):
			new_author = authorSchema.load(author)
			db.session.add(new_author)
			db.session.commit()
			new_article_author = ArticleAuthor(article_id=newArticle.id, author_id=new_author.id, sequence_number=idx+1)
			db.session.add(new_article_author)


		db.session.commit()

		app.logger.info("1 item added in the db")  
			
		return jsonify({"message": "Pubmed Article Added successfully" }), 200

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
		
		# Parse results into groups of duplicates
		duplicate_records = []
		for _, ids in duplicate_groups:
			article_ids = list(map(int, ids.split(',')))
			duplicate_records.append(
				article_schema.dump(model) for model in model.query.filter(model.id.in_(article_ids)).all()
			)
		
		duplicates[field] = duplicate_records

	return duplicates

@article_bp.route("/duplicates",methods=['GET'])
@verify_internal_api_id
@verify_LIBRARYMANAGER_role
def find_duplicate_groups(session):
	fields = request.args.getlist('field')
	if fields == []:
		fields = ['pubmed_id','doi','title','pubmed_id']
	duplicates = find_duplicates(Article, fields)

	result = {}

	for field, groups in duplicates.items():
		result[field] = []
		for group in groups:
			result[field].append([article for article in group])

	return jsonify(result),200
