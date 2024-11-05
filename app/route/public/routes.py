import json
import os
from flask import jsonify,current_app as app, render_template, request

from app.decorator import verify_GUEST_role
from app.schema import ArticleSchema
from app.util import nbibFileReader, risFileReader
from . import public_bp
from app.extension import db

@public_bp.route("/")
def index():
	return "This is The waiting list public route"


# @public_bp.route("/search")
# @verify_user
# def search_public():
#     keywords =  request.args.getlist('keyword')
#     startYear =  request.args.getlist('startYear')
#     endYear =  request.args.getlist('endYear')
#     authorName =  request.args.getlist('authorName')
#     titleText =  request.args.getlist('titleText')
	
	
#     query = request.args.get('q')
 

	
#     return 



def allowed_file(filename):
	"""Check if the file has the correct .ris extension."""
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['ris','nbib']

@public_bp.route('/upload_ris', methods=['POST'])
@verify_GUEST_role
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
		
		myjson = risFileReader(filepath=file_path)

		
		schema = ArticleSchema(many=True)
		objects = schema.load(myjson)
		for object in objects:
			db.session.add(object)
		db.session.commit()
		
		app.logger.info(f"{len(objects)} added in the db")  
		# Here you could add any processing logic for the RIS file
		
		return jsonify({"message": "File uploaded successfully", "filename": filename,"length":len(objects)}), 200
	else:
		return jsonify({"error": "Invalid file type. Only .ris files are allowed."}), 400




@public_bp.route('/upload_nbib', methods=['POST'])
@verify_GUEST_role
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
		
		myjson = nbibFileReader(filepath=file_path)

		
		schema = ArticleSchema(many=True)
		objects = schema.load(myjson)
		for object in objects:
			db.session.add(object)
		db.session.commit()
		
		app.logger.info(f"{len(objects)} added in the db")  
		# Here you could add any processing logic for the RIS file
		
		return jsonify({"message": "File uploaded successfully", "filename": filename,"length":len(objects)}), 200
	else:
		return jsonify({"error": "Invalid file type. Only nbib files are allowed."}), 400
