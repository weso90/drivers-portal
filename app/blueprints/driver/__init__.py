from flask import Blueprint

driver_bp = Blueprint('driver', __name__, url_prefix='/driver')

from app.blueprints.driver import routes