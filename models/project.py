from . import db


project_skills = db.Table(
    'project_skills',
    db.Column('project_id', db.Integer, db.ForeignKey('projects.id'), primary_key=True),
    db.Column('skill_id', db.Integer, db.ForeignKey('skills.id'), primary_key=True),
)


class Project(db.Model):
    __tablename__ = 'projects'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(256), nullable=False)
    description = db.Column(db.Text, nullable=True)
    domain = db.Column(db.String(128), nullable=True)
    difficulty = db.Column(db.String(32), nullable=True)

    required_skills = db.relationship('Skill', secondary=project_skills, backref='projects')

    def __repr__(self):
        return f'<Project {self.title}>'
