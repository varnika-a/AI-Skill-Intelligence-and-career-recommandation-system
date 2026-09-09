from datetime import datetime
from . import db


class Recommendation(db.Model):
    __tablename__ = 'recommendations'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    item_type = db.Column(db.String(32), nullable=False)  # 'skill' or 'project'
    item_id = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
    explanation = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Recommendation {self.item_type}={self.item_id} score={self.score}>'
