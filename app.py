from flask import Flask
from application.database import db
from datetime import datetime
app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Use a strong, random string

def creaate_app():
    app = Flask(__name__)
    app.debug = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///parking.sqlite3"
    db.init_app(app)
    app.app_context().push() #runtime error, bring everything under context of flask application
    return app

app = creaate_app()
from application.controllers import *
# from application.models import * #indreect connection using controllers.py

if __name__=="__main__":
    app.run()