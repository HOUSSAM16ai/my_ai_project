from flask import Blueprint
# نعطي المخطط اسمًا فريدًا 'admin'
bp = Blueprint('admin', __name__, template_folder='templates')
from app.admin import routes