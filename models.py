import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class Endcard(db.Model):
    """Model for storing endcard conversion records"""
    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # 'image' or 'video'
    file_size = db.Column(db.Integer, nullable=False)  # size in bytes
    portrait_created = db.Column(db.Boolean, default=True)
    landscape_created = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Endcard {self.original_filename}>'
    
    def to_dict(self):
        """Convert the model to a dictionary for JSON response"""
        return {
            'id': self.id,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'portrait_created': self.portrait_created,
            'landscape_created': self.landscape_created,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }