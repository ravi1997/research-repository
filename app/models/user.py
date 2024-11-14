from sqlalchemy import DateTime, ForeignKey, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from app.extension import db, bcrypt
from datetime import datetime
from sqlalchemy import func

from enum import Enum

from app.util import getNewSalt

# ENUMS
class UserState(Enum):
    CREATED  = "created"
    ACTIVE   = "active"
    BLOCKED  = "blocked"
    DISABLED = "disabled"
    DELETED  = "deleted"

class UserRole(Enum):
    SUPERADMIN = "superadmin"
    LIBRARYMANAGER = "libraryManager"
    FACULTY = "faculty"
    RESIDENT = "resident"
    GUEST = "guest"

class ValidState(Enum):
    VALID = "valid"
    INVALID = "invalid"

# MAIN MODELS
class Client(db.Model):
    __tablename__ = "clients"  # Updated table name to be plural
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(DateTime, server_default=func.now())  # Corrected attribute name
    client_session_id = db.Column(db.String(64), index=True, unique=True, nullable=False)
    user_id = db.Column(db.Integer, ForeignKey('users.id'), index=True, nullable=True) 
    status = db.Column(SQLAlchemyEnum(ValidState), index=True, nullable=False)
    ip = db.Column(db.String(16), nullable=True)
    salt = db.Column(db.String(256),nullable=False)

    user = relationship("User", back_populates="clients")
    otp = relationship("OTP", back_populates="client")
    
    def __init__(self, client_session_id, user_id=None, ip=None):
        self.client_session_id = client_session_id
        self.user_id = user_id
        self.ip = ip
        self.salt = getNewSalt()
        self.status = ValidState.VALID

    def isValid(self):
        return self.status == ValidState.VALID

    def setStatus(self, status):
        self.status = status

    def __repr__(self):
        return (f"<Client(id={self.id}, client_session_id='{self.client_session_id}', "
                f"user_id={self.user_id}, status='{self.status}', ip='{self.ip}')>")

class OTP(db.Model):
    __tablename__ = "otps"  # Updated table name to be plural
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, ForeignKey('clients.id'), index=True, unique=True, nullable=False)  # Corrected table name
    otp = db.Column(db.String(7), nullable=False)
    created_at = db.Column(DateTime, server_default=func.now(), nullable=False)
    status = db.Column(SQLAlchemyEnum(ValidState), index=True, nullable=False, server_default=f'{ValidState.VALID}')
    sendAttempt = db.Column(db.Integer, server_default="0")

    client = relationship("Client", back_populates="otp")
    
    def __init__(self, client_id, otp,status=ValidState.VALID):
        self.client_id = client_id
        self.otp = otp
        self.status = status

    def isValid(self):
        return self.status == ValidState.VALID

    def __repr__(self):
        return (f"<OTP(id={self.id}, client_id={self.client_id}, otp='{self.otp}', "
                f"status='{self.status}', created_at='{self.created_at}')>")

class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(30), index=True, nullable=False)
    middlename = db.Column(db.String(30), index=True, nullable=True)
    lastname = db.Column(db.String(30), index=True, nullable=True)
    mobile = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(30), nullable=False)

    department= db.Column(db.String(30), nullable=False)
    designation= db.Column(db.String(30), nullable=False)
    date_expiry= db.Column(DateTime, nullable=False)

    roles = relationship("UserRoles", back_populates="user")
    status = db.Column(SQLAlchemyEnum(UserState), index=True, nullable=False, server_default=f'{UserState.CREATED}')
    employee_id = db.Column(db.String(20),nullable=False,unique=True)

    created_at = db.Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = db.Column(DateTime, server_default=func.now(), nullable=False)
    wrongAttempt = db.Column(db.Integer,nullable=False, server_default="0")

    clients = relationship("Client", back_populates="user")

    def __init__(self, firstname, mobile,email,employee_id,department,designation,date_expiry, middlename=None, lastname=None,
                 status=UserState.CREATED, updated_at=None,roles = []):
        self.firstname = firstname
        self.middlename = (middlename if middlename else None)
        self.lastname = (lastname if lastname else None)


        self.employee_id = employee_id

        self.mobile = mobile
        self.email = email
        self.status = status

        self.department=department
        self.designation =designation
        self.date_expiry=date_expiry

        self.roles = roles
        if updated_at is not None:
            self.updated_at = updated_at

    def __repr__(self):
        return (f"<User(id={self.id}, name='{self.firstname} {self.middlename or ''} {self.lastname or ''}', "
                f"mobile='{self.mobile}', employee_id = '{self.employee_id}'"
                f"status='{self.status}', role='{self.role}')>")


    def isDeleted(self):
        return self.status == UserState.DELETED
    
    def isActive(self):
        return self.status == UserState.ACTIVE
    
    def isBlocked(self):
        return self.status == UserState.BLOCKED
    
    def has_role(self, role):
        return any(ur.role == role for ur in self.roles)


class UserRoles(db.Model):
    __tablename__ = 'user_roles'
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), primary_key=True)
    role = db.Column(SQLAlchemyEnum(UserRole),nullable=False)  # Use enum directly

    user = relationship("User", back_populates="roles")  # Backref to User
