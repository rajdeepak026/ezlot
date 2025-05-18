from .database import db # check for this file in the folder you are existing

class User(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(), unique=True, nullable=False)
    pwd = db.Column(db.String(),nullable=False)
    fullname=db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), nullable=False)
    pincode = db.Column(db.String(), nullable=False)
    type = db.Column(db.String(), default="general")
    detais = db.relationship("Info", backref="creator")

class Info(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    parking = db.Column(db.String(), nullable=False)
    status = db.Column(db.String(), nullable=False)
    location = db.Column(db.String(), nullable=False)
    address = db.Column(db.String(), nullable=False)
    pincode = db.Column(db.String(), nullable=False)
    price = db.Column(db.String(), nullable=False)
    maxispot = db.Column(db.String(), nullable=False)
    vehicle_no = db.Column(db.String(), nullable=True)
    timestamp = db.Column(db.DateTime(), nullable=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("user.id"), nullable=False)

