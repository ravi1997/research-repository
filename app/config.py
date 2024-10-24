import os
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))

class BaseConfig:
    DB_NAME = "backend"

class DevConfig(BaseConfig):
    load_dotenv('.env')
    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL')
    JWT_ACCESS_TOKEN_EXPIRES = os.getenv('JWT_ACCESS_TOKEN_EXPIRES')

    if JWT_ACCESS_TOKEN_EXPIRES is not None:
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=float(JWT_ACCESS_TOKEN_EXPIRES))
    
    SCHEDULER_JOBSTORES = {
        "default": SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
    }

class ProdConfig(BaseConfig):
    load_dotenv('.env.production')
    DEBUG = False
    SECRET_KEY = os.getenv('SECRET_KEY', 'default_secret_key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'app.db'))

    DB_ENGINE = os.getenv('DB_ENGINE') # mysql+pymysql
    DB_USER = os.getenv('DB_USER') # root
    DB_PASSWORD = os.getenv('DB_PASSWORD') # password
    DB_HOST = os.getenv('DB_HOST') # localhost
    DB_PORT = os.getenv('DB_PORT') # 3306
    DB_NAME = os.getenv('DB_NAME') # backend

    if all([DB_ENGINE, DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB_NAME]):
        SQLALCHEMY_DATABASE_URI = f'{DB_ENGINE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')

    JWT_ACCESS_TOKEN_EXPIRES = os.getenv('JWT_ACCESS_TOKEN_EXPIRES')

    if JWT_ACCESS_TOKEN_EXPIRES is not None:
        JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=float(JWT_ACCESS_TOKEN_EXPIRES))
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    SCHEDULER_JOBSTORES = {
        "default": SQLAlchemyJobStore(url=SQLALCHEMY_DATABASE_URI)
    }

    SCHEDULER_API_ENABLED = True
