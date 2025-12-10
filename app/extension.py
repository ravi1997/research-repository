# EXTENSIONS
from flask_bcrypt import Bcrypt
from flask_apscheduler import APScheduler
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache


db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
bcrypt = Bcrypt() 
scheduler = APScheduler()
cache = Cache(config={'CACHE_TYPE': 'simple'})