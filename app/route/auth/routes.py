from datetime import datetime
import json
from pprint import pprint
import uuid
from flask import jsonify,current_app as app
from marshmallow import ValidationError
from sqlalchemy import func
from dateutil import parser
from app.decorator import checkBlueprintRouteFlag, verify_GUEST_role, verify_SUPERADMIN_role, verify_body, verify_user
from app.models import OTP, User
from app.extension import db,scheduler
from app.models.user import UserRole, UserRoles, UserState, ValidState
from app.schema import UserSchema
from app.utility import  cdac_service, generate_otp, send_sms
from . import auth_bp

@auth_bp.route("/")
@checkBlueprintRouteFlag
@verify_SUPERADMIN_role
def index(session):
    return "This is The waiting list auth route"


def delete_OTP(id):
    with app.app_context():
        # print(jwt)
        otp = OTP.query.filter(
            id == id
        ).first()
        if otp:
            db.session.delete(otp)
            db.session.commit()
        else:
            app.logger.error(f"for deletion of OTP : {id} not found")


@auth_bp.route("/login", methods=["POST"])
@verify_GUEST_role
@verify_body
def login(data,session):
    try:
        if not 'employee_id' in data:
            app.logger.error("Employee Id is compulsory")
            return jsonify({"message":"Employee Id is compulsory"}),401
        
        employee_id = data['employee_id']
        
        
        user = User.query.filter_by(
            employee_id=employee_id
        ).one_or_none()
        if not user:
            response = cdac_service(employee_id)
            if type(response) is str:
                return jsonify({"message":"Something went wrong. Either employee id not valid or server error"}),500
            
            response = response["Data"][0]
            name = response["name"].split()
            if len(name) <= 2:
                firstname = name[0]
                lastname = name[1] 
            else:
                fname = name
                lastname = fname.pop()
                firstname = "".join(fname)                
            
            roles = []
            if "Professor".lower() in response["designation"].lower() or "Head of Department".lower() in response["designation"].lower():
                roles = [UserRoles(role=UserRole.FACULTY)]
            elif "resident".lower() in response["designation"].lower():
                roles = [UserRoles(role=UserRole.RESIDENT)]
            elif "scientist".lower() in response["designation"].lower():
                roles = [UserRoles(role=UserRole.SCIENTIST)]
            elif "librarian".lower() in response["designation"].lower() or "library attendent".lower() in response["designation"].lower():
                roles = [UserRoles(role=UserRole.LIBRARYMANAGER)]
            


            user = User(
                firstname = firstname,
                middlename = "",
                lastname = lastname,
                mobile = response["mobile_number"],
                email = response["email_address"],
                department= response["department"],
                designation=  response["designation"],
                date_expiry= parser.parse(response["retirement_date"]),
                roles=roles,
                employee_id = employee_id
            )
            
            db.session.add(user)
            db.session.commit()
            
        if user.isDeleted():
            app.logger.error(f"Account is deleted : {employee_id}")
            return jsonify({"message":"Account is either deleted or blocked. Please contact admin."}),401

        if user.isBlocked():
            app.logger.error(f"Account is blocked : {employee_id}")
            return jsonify({"message":"Account is either deleted or blocked. Please contact admin."}),401

        new_otp = ""
        phone = user.mobile
        found=False

        if session.otp != []:
            valid = False
            for otp in session.otp :
                app.logger.info(f"Looping otps in session.otp {session.otp}")
                if otp.isValid():
                    app.logger.info(f"OTP otp.isValid is True {otp.isValid}")
                    valid = True
                    otp = OTP.query.filter_by(id = otp.id).one_or_none()
                    app.logger.info(f"Filtering OTPs  otp.id {otp.id} otp = {otp}")
                    if otp is None:
                        if app.config['OTP_GENERATION']:
                            new_otp = generate_otp()
                        else:
                            new_otp = "123456"
                    else:
                        new_otp = otp.otp
                        otp.sendAttempt = otp.sendAttempt + 1
                        found = True

            if not valid:
                if app.config['OTP_GENERATION']:
                    new_otp = generate_otp()
                else:
                    new_otp = "123456" 
        else:
            if app.config['OTP_GENERATION']:
                new_otp = generate_otp()
            else:
                new_otp = "123456"            
        
        message = f'Your OTP for Login in AIIMS is {new_otp}'
        if not found:
            app.logger.info(f"NOT FOUND")
            otp = OTP(client_id=session.id,otp=new_otp)
            app.logger.info(f"runnin OTP Function session id  = {session.id} OTP = {new_otp} - running  db.session.add(otp))")
            db.session.add(otp)


        if app.config['OTP_FLAG']:
            sms_status = send_sms(phone,message)
            if sms_status == 200:
                app.logger.info(f"Sent SMS Status = {sms_status} - comitting to session ")
                db.session.commit()
                if not found:
                    scheduler.add_job(
                        str(uuid.uuid4()),
                        delete_OTP,
                        trigger="date",
                        run_date=datetime.now() + app.config['OTP_DELTA'],
                        args=[otp.id],
                    )
                
                return jsonify({"message":"OTP has been generated"}),200
            else:
                db.session.rollback()
                app.logger.error(f"ROLLING BACK otp ")
                return jsonify({"message":"something went wrong. Please try again."}),500
        else:
            db.session.commit()
            return jsonify({"message":"OTP has been generated"}),200

    except ValidationError as err:
        app.logger.error(f"error {err.messages}")
        # Return a nice message if validation fails
        return jsonify({"message":err.messages}),401


@auth_bp.route("/verify_otp", methods=["POST"])
@verify_GUEST_role
@verify_body
def verifyOTP(data,session):
    user_schema = UserSchema()
    try:
        if not 'OTP' in data:
            app.logger.error("OTP is compulsory")
            return jsonify({"message":"OTP is compulsory"}),401
        
        if not 'employee_id' in data:
            app.logger.error("Employee Id is compulsory")
            return jsonify({"message":"Employee Id is compulsory"}),401
        
        employee_id = data['employee_id']
        
        current_otp = data['OTP']
        
        # Convert validated request schema into a User object
        otp = None
        for otp_t in session.otp:
            if otp_t.isValid():
                otp = otp_t
                
        if otp is None:
            return jsonify({"message":"Something went wrong. Please reload the site."}),401
        
        otp_data = otp.otp

        user = User.query.filter_by(
            employee_id=employee_id
        ).one_or_none()
        
        otp = OTP.query.filter_by(id=otp.id).first()
        otp.status = ValidState.INVALID

        if not user:
            app.logger.error(f"Account does not exist : {employee_id}")
            app.logger.error(f"Invalid request")
            session.status = ValidState.INVALID
            db.session.commit()
            return jsonify({"message":"Invalid request"}),401

        if user.isDeleted() or user.isBlocked():
            app.logger.error(f"Account {employee_id} is deleted or blocked.Please contact admin.")
            session.status = ValidState.INVALID
            db.session.commit()
            return jsonify({"message":"Invalid request"}),401

        if otp_data != current_otp:    
            user.wrongAttempt += 1
            attempt = app.config['OTP_MAX_ATTEMPT'] - user.wrongAttempt
            message = f"Wrong OTP.Attempt left : {attempt}"
            if user.wrongAttempt == 3:
                user.status = UserState.BLOCKED
                otp.status = ValidState.INVALID
                db.session.commit()
                message += " Account is blocked"
            return jsonify({"message":message}),401
        else:
            user.wrongAttempt = 0
            session.user_id = user.id
            db.session.commit()

            return jsonify(
                message = "successfull login",
                user=user_schema.dump(user),
            ),200

    except ValidationError as err:
        # Return a nice message if validation fails
        return jsonify({"message":err.messages}),400

@auth_bp.route("/logout", methods=["GET"])
@verify_user
def logout(session):
    current_user = session.user_id
    session.user_id = None
    db.session.commit()
    return jsonify(logged_in_as=current_user), 200
