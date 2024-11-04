from sqlalchemy import Text

import logging
import os
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from app.config import DevConfig
from app.logger import SQLAlchemyHandler
from .extension import db, migrate,ma,bcrypt,scheduler
from .route.main import main_bp
from .route.auth import auth_bp
from .route.public import public_bp
from .route.user import user_bp
from app.extra import job_listener
from apscheduler.events import EVENT_JOB_EXECUTED
from app.db_initializer import seed_db_command, empty_db_command,test_command
from app.models import *

def create_app():
    app = Flask(__name__,static_folder='web')
    app.config.from_object(DevConfig)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)
    bcrypt.init_app(app)
    scheduler.init_app(app)
    scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED)
    CORS(app)
    scheduler.start()


    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    app.cli.add_command(seed_db_command)
    app.cli.add_command(test_command)
    app.cli.add_command(empty_db_command)


    # Configure SQLAlchemy logging handler
    sql_handler = SQLAlchemyHandler()
    sql_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
    )
    sql_handler.setFormatter(formatter)
    app.logger.addHandler(sql_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info("Flask app startup")




    @app.errorhandler(404)
    def page_not_found(e):
        # Get the URL that caused the error
        url = request.url
        method = request.method
        app.logger.info(f"main app route : {url} {method}")
        return jsonify({"message":f"Url not found : {url} {method}"}),404
        

    # Register blueprints
    app.register_blueprint(main_bp, url_prefix="/researchrepository")
    app.register_blueprint(auth_bp, url_prefix="/researchrepository/auth")
    app.register_blueprint(public_bp, url_prefix="/researchrepository/public")
    app.register_blueprint(user_bp, url_prefix="/researchrepository/user")
    return app
