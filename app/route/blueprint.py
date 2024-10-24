
# Registering Blueprints		
from flask import Blueprint

adminSuperAdmin_bp = Blueprint('adminSuperAdmin', __name__)

main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__)

# STRING BLUEPRINTS
diagnosis_bp = Blueprint('daignosis', __name__)
plan_bp = Blueprint('plan', __name__)
eye_bp = Blueprint('eye', __name__)
priority_bp = Blueprint('priority', __name__)
anesthesia_bp = Blueprint('anesthesia', __name__)
eua_bp = Blueprint('eua', __name__)
short_bp = Blueprint('short', __name__)

# MAIN BLUEPRINT``
patientdemographic_bp = Blueprint('patientdemographic', __name__)

patiententry_bp = Blueprint('patiententry', __name__)

building_bp = Blueprint('building', __name__)
floor_bp = Blueprint('floor', __name__)
room_bp = Blueprint('room', __name__)
account_bp = Blueprint('account', __name__)
role_bp = Blueprint('role', __name__)
department_bp = Blueprint('department', __name__)
unit_bp = Blueprint('unit', __name__)
designation_bp = Blueprint('designation', __name__)
cadre_bp = Blueprint('cadre', __name__)
user_bp = Blueprint('user', __name__)
block_bp = Blueprint('block', __name__)
centre_bp = Blueprint('centre', __name__)
public_bp = Blueprint('public',__name__)