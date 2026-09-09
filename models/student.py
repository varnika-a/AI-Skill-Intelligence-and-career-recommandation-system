from datetime import datetime
from . import db


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(128), unique=True, nullable=True)
    education = db.Column(db.String(256), nullable=True)
    semester = db.Column(db.String(32), nullable=True)
    interests = db.Column(db.String(512), nullable=True)
    career_goal = db.Column(db.String(256), nullable=True)
    resume_filename = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    skills = db.relationship('StudentSkill', back_populates='student', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Student {self.name} ({self.id})>'
