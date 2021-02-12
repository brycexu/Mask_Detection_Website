"""
The model module where models are registered
"""
from db import db

'''
from flask import Flask
app = Flask(__name__)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:xuxianda6403838@127.0.0.1:3306/project1'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True
app.config['SECRET_KEY'] = 'ece1779'
db = SQLAlchemy(app)
migrate = Migrate(app, db)
'''

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(64))
    def __str__(self):
        return 'User{name=%s}' % self.username

class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(64))
    def __str__(self):
        return 'Admin{name=%s}' % self.username

class FaceImage(db.Model):
    __tablename__ = 'images'
    id = db.Column(db.Integer, primary_key=True)
    # 0: No face
    # 1: All faces wear masks
    # 2: All faces not wear masks
    # 3: Some faces wear masks
    category = db.Column(db.Integer, nullable=False)
    path = db.Column(db.String(128), nullable=False)

if __name__ == '__main__':
    db.create_all()