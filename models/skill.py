from datetime import datetime
from . import db


class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), unique=True, nullable=False)
    category = db.Column(db.String(64), nullable=True)
    description = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<Skill {self.name}>'


class StudentSkill(db.Model):
    __tablename__ = 'student_skills'
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), primary_key=True)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), primary_key=True)
    proficiency_score = db.Column(db.Float, default=0.0)
    self_report = db.Column(db.Float, nullable=True)
    evidence = db.Column(db.Text, nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('Student', back_populates='skills')
    skill = db.relationship('Skill')


class SkillRelationship(db.Model):
    __tablename__ = 'skill_relationships'
    id = db.Column(db.Integer, primary_key=True)
    source_skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    target_skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    relationship_type = db.Column(db.String(64), nullable=False)
    strength = db.Column(db.Float, default=1.0)

    source = db.relationship('Skill', foreign_keys=[source_skill_id])
    target = db.relationship('Skill', foreign_keys=[target_skill_id])
