from flask import Blueprint

article_bp = Blueprint('article', __name__)

from . import routes
