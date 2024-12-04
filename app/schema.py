from flask_marshmallow import Marshmallow
from marshmallow import fields, EXCLUDE,validate

from app.models import OTP, Client, User, Article,Author
from app.models.article import ArticleAuthor, ArticleStatistic, Keyword, Link, PublicationType

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

class ArticleAuthorSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArticleAuthor
        load_instance = True
        include_fk = True  # Include foreign keys

    author = fields.Nested(AuthorSchema)  # Include full Author object



class KeywordSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Keyword
        load_instance = True
        include_fk = True  # Include foreign keys
    articles = fields.Nested("ArticleSchema",many=True,exclude=('keywords',))

    def get_authors(self, obj):
        if not obj.authors:
            return []
        return AuthorSchema(many=True).dump(
            [article_author.author for article_author in obj.authors]
        )

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
    articles = fields.Method("get_articles") 
    
    def get_articles(self, obj):
        if not obj.articles:
            return []
        # Exclude the 'authors' field from the ArticleSchema
        return ArticleSchema(many=True, exclude=("authors",)).dump(
            [article_author.article for article_author in obj.articles]
        )


class ArticleStatisticSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ArticleStatistic
        load_instance = True
        include_fk = True  # Include foreign keys
    article = fields.Nested("ArticleSchema",exclude=('statistic',))

class ArticleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Article
        load_instance = True
        include_fk = True

    authors = fields.Method("get_authors")  # Use a custom method to serialize authors

    def get_authors(self, obj):
        if not obj.authors:
            return []
        return AuthorSchema(many=True, exclude=("articles",)).dump(
            [article_author.author for article_author in obj.authors]
        )

    
    
    keywords = fields.Nested(KeywordSchema,many=True,exclude=('articles',))  # Avoid circular dependency
    links = fields.Nested(LinkSchema,many=True,validate=validate.Length(min=0),exclude=('article',))  # Avoid circular dependency
    publication_types= fields.Nested(PublicationTypeSchema,many=True,validate=validate.Length(min=1),exclude=('articles',))  # Avoid circular dependency
    statistic = fields.Nested(ArticleStatisticSchema,exclude=('article',))  # Avoid circular dependency
    