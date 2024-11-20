import os
from pprint import pprint
from flask import jsonify,current_app as app, request
from marshmallow import ValidationError

from app.decorator import checkBlueprintRouteFlag, verify_SUPERADMIN_role, verify_USER_role, verify_body, verify_internal_api_id, verify_session
from app.extension import db,scheduler
from app.models.article import Article
from app.schema import ArticleSchema
from app.util import download_xml, fileReader,  parse_pubmed_xml
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
	per_page = 10  # Number of items per page
	articles_schema = ArticleSchema(many=True)
	articles = Article.query.order_by(Article.publication_date.desc()).all()
	data = articles_schema.dump(articles)
	# Implement pagination logic
	start = (page - 1) * per_page
	end = start + per_page
	paginated_data = data[start:end]
	
	return jsonify({
		'data': paginated_data,
		'page': page,
		'total_pages': len(data) // per_page + (1 if len(data) % per_page > 0 else 0)
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

def allowed_file(filename):
	"""Check if the file has the correct .ris extension."""
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['ris','nbib']

@article_bp.route('/upload_ris', methods=['POST'])
@verify_USER_role
def upload_ris(session):
	# Check if the file part is present in the request
	if 'file' not in request.files:
		return jsonify({"error": "No file part in the request"}), 400

	file = request.files['file']

	# Check if a file was submitted
	if file.filename == '':
		return jsonify({"error": "No file selected"}), 400

	# Check if the file is allowed
	if file and allowed_file(file.filename):
		filename = file.filename
		file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
		
		# Save the file
		file.save(file_path)
		
		myjson = fileReader(filepath=file_path)

		
		schema = ArticleSchema(many=True)
		objects = schema.load(myjson)
		for object in objects:
			db.session.add(object)
		db.session.commit()
		
		app.logger.info(f"{len(objects)} added in the db")  
		# Here you could add any processing logic for the RIS file
		
		return jsonify({"message": "File uploaded successfully", "filename": filename,"length":len(objects)}), 200
	else:
		return jsonify({"error": "Invalid file type. Only .ris files are allowed."}), 401


@article_bp.route('/upload_nbib', methods=['POST'])
@verify_USER_role
def upload_nbib(session):
	# Check if the file part is present in the request
	if 'file' not in request.files:
		return jsonify({"error": "No file part in the request"}), 400

	file = request.files['file']

	# Check if a file was submitted
	if file.filename == '':
		return jsonify({"error": "No file selected"}), 400

	# Check if the file is allowed
	if file and allowed_file(file.filename):
		filename = file.filename
		file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
		
		# Save the file
		file.save(file_path)
		
		myjson = fileReader(filepath=file_path)
		# pprint(myjson)
		schema = ArticleSchema(many=True)
		objects = schema.load(myjson)
		for object in objects:
			db.session.add(object)
		db.session.commit()
		
		app.logger.info(f"{len(objects)} added in the db")  
		# Here you could add any processing logic for the RIS file
		
		return jsonify({"message": "File uploaded successfully", "filename": filename,"length":len(objects)}), 200
	else:
		return jsonify({"error": "Invalid file type. Only nbib files are allowed."}), 401


@article_bp.route('/pubmedFectch', methods=['POST'])
@verify_USER_role
@verify_body
def pubmedFectch(data,session):
	pubmed_id = data["pmid"]

	filename = os.path.join(app.config["UPLOAD_FOLDER"],'pubfetch',f'pubmed-{pubmed_id}.xml')

	success = download_xml(pubmed_id,filename)
	if success:
		myjson = parse_pubmed_xml(filename)
		
		schema = ArticleSchema()
		# pprint(myjson)

		object = schema.load(myjson)
		db.session.add(object)
		db.session.commit()
		app.logger.info("1 item added in the db")  
			
		return jsonify({"message": "Pubmed Article Added successfully" }), 200

	else:
		return jsonify({"message":"Either you provided wrong Pubmed ID or something went wrong."}),401