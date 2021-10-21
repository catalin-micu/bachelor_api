from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from flask_cors import CORS

con_url = 'postgresql://postgres:password@localhost:5432/anpr'
engine = create_engine(con_url, isolation_level='AUTOCOMMIT')
Session = sessionmaker(bind=engine)
session = Session()


def create_app():
    app = Flask(__name__)
    CORS(app)

    from views import main
    app.register_blueprint(main)

    return app
