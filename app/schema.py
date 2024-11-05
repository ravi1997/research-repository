from flask_marshmallow import Marshmallow
from marshmallow import fields, EXCLUDE,validate

from app.models import OTP, Client, Log, User, Article,Author
from app.models.article import Keyword, Link, PublicationType

ma = Marshmallow()

# Schemas for the models
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True  # Include foreign keys

    clients = fields.Nested('ClientSchema', many=True, exclude=('user',))  # Avoid circular dependency


class ClientSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Client
        load_instance = True
        include_fk = True

    user = fields.Nested(UserSchema, exclude=('clients',))  # Avoid circular dependency


class OTPSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = OTP
        load_instance = True
        include_fk = True

    client = fields.Nested(ClientSchema, exclude=('otps',))  # Avoid circular dependency


class LogSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Log
        load_instance = True
        include_fk = True

class GuestClientSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Client
        load_instance = True
        include_fk = True



class AuthorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Author
        load_instance = True
        include_fk = True  # Include foreign keys
    articles = fields.Nested("ArticleSchema",many=True,exclude=('authors',))

class KeywordSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Keyword
        load_instance = True
        include_fk = True  # Include foreign keys
    articles = fields.Nested("ArticleSchema",many=True,exclude=('keywords',))


class LinkSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Link
        load_instance = True
        include_fk = True  # Include foreign keys
    article = fields.Nested("ArticleSchema",exclude=('links',))

class PublicationTypeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = PublicationType
        load_instance = True
        include_fk = True  # Include foreign keys
    articles = fields.Nested("ArticleSchema",exclude=('publication_types',))


class ArticleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Article
        load_instance = True
        include_fk = True

    authors = fields.Nested(AuthorSchema,many=True,exclude=('articles',))  # Avoid circular dependency
    keywords = fields.Nested(KeywordSchema,many=True,exclude=('articles',))  # Avoid circular dependency
    links = fields.Nested(LinkSchema,many=True,validate=validate.Length(min=0),exclude=('article',))  # Avoid circular dependency
    publication_types= fields.Nested(PublicationTypeSchema,many=True,validate=validate.Length(min=1),exclude=('articles',))  # Avoid circular dependency