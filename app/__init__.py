# app/__init__.py - هذا الملف صحيح، لا تغيره
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'routes.login' 
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # هذا هو السطر الصحيح الذي يسجل الـ blueprint المبسط
    from app.routes import routes as routes_blueprint
    app.register_blueprint(routes_blueprint)

    return app