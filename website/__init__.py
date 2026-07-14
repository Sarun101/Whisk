from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

DB_NAME = "database.db"


def create_app():
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = 'random_gibberish_string_of_character_I_will_Not_need'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'
    
    db.init_app(app)
    
    from .auth import auth
    
    app.register_blueprint(auth,url_prefix = '/')
    
    with app.app_context():
        db.create_all()
    
    return app