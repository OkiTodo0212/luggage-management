from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

class Luggage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    remarks = db.Column(db.String(200), nullable=True)
    luggage_quantity = db.Column(db.Integer, nullable=False)
    mail_quantity = db.Column(db.Integer, nullable=False)
    time_add=db.Column(db.DateTime,nullable = False,default=datetime.now(pytz.timezone('Asia/Tokyo')))
    time_receive=db.Column(db.DateTime,nullable = True,default=None)
    person_id = db.Column(db.Integer, db.ForeignKey('person.id'), nullable=False)
    flag_received = db.Column(db.Boolean,default=False)

class Person(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dormitory = db.Column(db.String(10),nullable=False)
    room_number = db.Column(db.Integer, nullable=False)
    last_name = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(20), nullable=False)
    furigana = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), unique=True, nullable=False)
    luggage_all = db.Column(db.Integer, nullable=True, default=0)
    mail_all = db.Column(db.Integer, nullable=True, default=0)
    luggage = db.relationship('Luggage', backref='owner', lazy=True)