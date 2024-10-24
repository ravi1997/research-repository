from flask import jsonify,current_app, request

from app.decorator import verify_user
from . import public_bp


@public_bp.route("/")
def index():
    return "This is The waiting list public route"


@public_bp.route("/search")
@verify_user
def search_public():
    keywords =  request.args.getlist('keyword')
    startYear =  request.args.getlist('startYear')
    endYear =  request.args.getlist('endYear')
    authorName =  request.args.getlist('authorName')
    titleText =  request.args.getlist('titleText')
    
    
    query = request.args.get('q')
 

    
    return 