from flask import jsonify,current_app as app
from marshmallow import ValidationError

from app.decorator import verify_session
from app.extension import db,scheduler
from app.models.article import Article
from app.schema import ArticleSchema
from . import article_bp

@article_bp.route("/")
def index():
    return "This is The waiting list article route"

@article_bp.route("/table")
@verify_session
def generateTable():
    articles_schema = ArticleSchema(many=True)
    articles = Article.query.