from flask import jsonify,current_app as app, request
from marshmallow import ValidationError

from app.decorator import verify_session
from app.extension import db,scheduler
from app.models.article import Article
from app.schema import ArticleSchema
from . import article_bp

@article_bp.route("/")
def index():
    return "This is The research repository article route"

@article_bp.route("/table")
@verify_session
def generateTable(session):
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Number of items per page
    articles_schema = ArticleSchema(many=True)
    articles = Article.query.all()
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
    