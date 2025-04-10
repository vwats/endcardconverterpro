import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(db.Model):
    """Model for storing user data"""
    id = db.Column(db.Integer, primary_key=True)
    replit_id = db.Column(db.String(255), unique=True)
    credits = db.Column(db.Integer, default=1)  # New users get 1 free credit
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Endcard(db.Model):
    """Model for storing endcard conversion records"""
    id = db.Column(db.Integer, primary_key=True)
    
    # Portrait file details
    portrait_filename = db.Column(db.String(255), nullable=True)
    portrait_file_type = db.Column(db.String(10), nullable=True)  # 'image' or 'video'
    portrait_file_size = db.Column(db.Integer, nullable=True)  # size in bytes
    portrait_created = db.Column(db.Boolean, default=False)
    
    # Landscape file details
    landscape_filename = db.Column(db.String(255), nullable=True)
    landscape_file_type = db.Column(db.String(10), nullable=True)  # 'image' or 'video'
    landscape_file_size = db.Column(db.Integer, nullable=True)  # size in bytes
    landscape_created = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Endcard {self.id}: {self.portrait_filename or "No portrait"} / {self.landscape_filename or "No landscape"}>'
    
    def to_dict(self):
        """Convert the model to a dictionary for JSON response"""
        return {
            'id': self.id,
            'portrait_filename': self.portrait_filename,
            'portrait_file_type': self.portrait_file_type,
            'portrait_file_size': self.portrait_file_size,
            'portrait_created': self.portrait_created,
            'landscape_filename': self.landscape_filename,
            'landscape_file_type': self.landscape_file_type,
            'landscape_file_size': self.landscape_file_size,
            'landscape_created': self.landscape_created,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }