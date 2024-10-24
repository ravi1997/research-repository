from flask_marshmallow import Marshmallow
from marshmallow import fields, EXCLUDE

from app.models import OTP, Client, Log, Organisation, User

ma = Marshmallow()

# Schemas for the models
class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        include_fk = True  # Include foreign keys

    clients = fields.Nested('ClientSchema', many=True, exclude=('user',))  # Avoid circular dependency


class OrganisationSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Organisation
        load_instance = True
        include_fk = True

    users = fields.Nested(UserSchema, many=True, exclude=('organisation',))  # Avoid circular dependency


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
