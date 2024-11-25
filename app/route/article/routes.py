import os
from pprint import pprint
from flask import jsonify,current_app as app, request
from marshmallow import ValidationError

from app.decorator import checkBlueprintRouteFlag, verify_SUPERADMIN_role, verify_USER_role, verify_body, verify_internal_api_id, verify_session
from app.extension import db,scheduler
from app.models.article import Article, ArticleAuthor, ArticleKeyword, ArticlePublicationType, Author, Keyword, PublicationType
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
		author_schema = AuthorSchema()
		
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
	
					old_author = None
					if new_author.affiliations:
						old_author = Author.query.filter_by(
							fullName = new_author.fullName,
							author_abbreviated = new_author.author_abbreviated,
							affiliations = new_author.affiliations
						).first()
					if old_author:
						new_article_author = ArticleAuthor(article_id=newArticle.id, author_id=old_author.id, sequence_number=idx+1)
					else:
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

			old_author = None
			if new_author.affiliations:
				old_author = Author.query.filter_by(
					fullName = new_author.fullName,
					author_abbreviated = new_author.author_abbreviated,
					affiliations = new_author.affiliations
				).first()
			if old_author:
				new_article_author = ArticleAuthor(article_id=newArticle.id, author_id=old_author.id, sequence_number=idx+1)
			else:
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
	if article and article.id == data['id']:
		for key, value in data.items():
			if hasattr(article, key) and key !="id":  # Check if the object has the attribute
				setattr(article, key, value)
		db.session.commit()
		return jsonify({"message":"Updated Successfully"}),200
	else:
		return jsonify({"message":f"Article id {id} not found"}),404
