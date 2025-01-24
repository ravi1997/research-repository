from app.extension import db

class Subscriber(db.Model):
    __tablename__ = 'subscribers'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.Text, nullable=False)
    employee_id = db.Column(db.String(20),nullable=True)
    mailAllowed = db.Column(db.Integer,nullable=False, server_default="1")
    