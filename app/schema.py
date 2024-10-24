from flask_marshmallow import Marshmallow
from marshmallow import fields, EXCLUDE

from app.models import OTP, Client, Log, User, Article,Author

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


class ArticleSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Article
        load_instance = True
        include_fk = True

    authors = fields.Nested(AuthorSchema, exclude=('articles',))  # Avoid circular dependency
