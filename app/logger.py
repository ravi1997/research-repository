import logging
from flask import current_app
from .models import Log
from .extension import db

class SQLAlchemyHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record):
        try:
            if not current_app:
                return
            with current_app.app_context():
                log = Log(
                    level=record.levelname,
                    message=record.getMessage(),
                    pathname=record.pathname,
                    lineno=record.lineno,
                )
                db.session.add(log)
                db.session.commit()
        except Exception:
            self.handleError(record)
