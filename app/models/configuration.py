from app.extension import db


class Configuration(db.Model):
    __tablename__ = "configurations"  # Updated table name to be plural
    id = db.Column(db.Integer, primary_key=True)
    OTP_FLAG = db.Column(db.Boolean, nullable=False, server_default=f'{False}')
    LOG_VERBOSITY = db.Column(db.Integer,nullable=False, server_default="0")
    
    
    def getInstance():
        return Configuration.query.all()[0]
    
    def getOTPFlag():
        return Configuration.getInstance().OTP_Flag
    
    def getLogVerbosity():
        return Configuration.getInstance().LOG_VERBOSITY
    