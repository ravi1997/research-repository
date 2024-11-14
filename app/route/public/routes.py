import json
import os
from flask import jsonify,current_app as app, render_template, request

from app.decorator import verify_GUEST_role, verify_body
from app.schema import ArticleSchema
from app.util import download_xml, nbibFileReader, parse_pubmed_xml, risFileReader
from . import public_bp
from app.extension import db

@public_bp.route("/")
def index():
	return "This is The waiting list public route"
