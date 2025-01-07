import os
import uuid
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from dotenv import load_dotenv
from datetime import timedelta

basedir = os.path.abspath(os.path.dirname(__file__))


class BaseConfig:
    DB_NAME = "backend"
    OTP_FLAG = True
    OTP_GENERATION = True
    LOG_REQUEST = True
    LOG_RESPONSE = True
    OTP_DELTA = timedelta(minutes=30)    
    OTP_MAX_ATTEMPT = 3
    SALT_PASSWORD = "some_unique_code"
    COOKIE_AGE = 60*60*24
    API_ID = "43576556-30fd-483c-b95a-28da3a950388"
    BLUEPRINT_ROUTE = True
    

class DevConfig(BaseConfig):
    load_dotenv('.env')
    DEBUG = True
    SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")
    TEMPLATES_AUTO_RELOAD = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///' + os.path.join(basedir, 'app.db'))
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = os.getenv('MAIL_PORT')
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS')
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL')
    
    OTP_SERVER = os.getenv('OTP_SERVER')
    OTP_USERNAME = os.getenv('OTP_USERNAME')
    OTP_PASSWORD = os.getenv('OTP_PASSWORD')
    OTP_ID = os.getenv('OTP_ID')
    OTP_SENDERID = os.getenv('OTP_SENDERID')
    
    
    CDAC_USERNAME = os.getenv('CDAC_USERNAME')
    CDAC_PASSWORD = os.getenv('CDAC_PASSWORD')
    CDAC_AUTH_SERVER = os.getenv('CDAC_AUTH_SERVER')
    CDAC_SERVER = os.getenv('CDAC_SERVER')
    CDAC_ID = os.getenv('CDAC_ID')

    
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER')
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
