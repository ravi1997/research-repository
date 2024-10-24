from flask import jsonify,current_app
from marshmallow import ValidationError
from sqlalchemy import func

from app.decorator import verify_body
from app.models import Account, Building, BuildingFloors, Cadre, Department, DepartmentUnits, Designation, Floor, FloorRooms, Room, Unit,  User
from app.extension import db,bcrypt

from flask import jsonify

from app.schema import AccountSchema, BuildingSchema, CadreSchema, DepartmentSchema, DesignationSchema, FloorSchema, RoomSchema, UnitSchema, UserSchema
from app.util import generate_strong_password, send_sms
from . import public_bp


@public_bp.route("/")
def index():
    return "This is The waiting list public route"
