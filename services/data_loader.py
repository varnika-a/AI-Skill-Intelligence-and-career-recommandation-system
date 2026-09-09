import pandas as pd
from pathlib import Path
from models import db
from models.skill import Skill, SkillRelationship, StudentSkill
from models.project import Project
from models.student import Student


def _data_dir():
    return Path(__file__).resolve().parents[1] / 'data'


def load_skills(session):
    path = _data_dir() / 'skills.csv'
    df = pd.read_csv(path)
    added = 0
    for _, row in df.iterrows():
        name = str(row['name']).strip()
        if not name:
            continue
        existing = session.query(Skill).filter_by(name=name).first()
        if not existing:
            s = Skill(name=name, category=row.get('category'), description=row.get('description'))
            session.add(s)
            added += 1
    session.commit()
    return added


def load_skill_relationships(session):
    path = _data_dir() / 'skill_relationships.csv'
    df = pd.read_csv(path)
    added = 0
    for _, row in df.iterrows():
        src = str(row['source']).strip()
        tgt = str(row['target']).strip()
        rel = str(row.get('relationship_type', 'related'))
        strength = float(row.get('strength', 1.0))
        if not src or not tgt:
            continue
        source = session.query(Skill).filter_by(name=src).first()
        target = session.query(Skill).filter_by(name=tgt).first()
        if not source or not target:
            continue
        existing = session.query(SkillRelationship).filter_by(source_skill_id=source.id, target_skill_id=target.id, relationship_type=rel).first()
        if not existing:
            sr = SkillRelationship(source_skill_id=source.id, target_skill_id=target.id, relationship_type=rel, strength=strength)
            session.add(sr)
            added += 1
    session.commit()
    return added


def load_projects(session):
    path = _data_dir() / 'projects.csv'
    df = pd.read_csv(path)
    added = 0
    for _, row in df.iterrows():
        title = str(row['title']).strip()
        if not title:
            continue
        existing = session.query(Project).filter_by(title=title).first()
        if existing:
            continue
        p = Project(title=title, description=row.get('description'), domain=row.get('domain'), difficulty=row.get('difficulty'))
        # attach required_skills by name
        reqs = str(row.get('required_skills', '')).split(',') if not pd.isna(row.get('required_skills', '')) else []
        for r in reqs:
            name = r.strip()
            if not name:
                continue
            skill = session.query(Skill).filter_by(name=name).first()
            if skill:
                p.required_skills.append(skill)
        session.add(p)
        added += 1
    session.commit()
    return added


def load_students(session):
    path = _data_dir() / 'sample_students.csv'
    df = pd.read_csv(path)
    added = 0
    for _, row in df.iterrows():
        name = str(row['name']).strip()
        email = str(row.get('email')).strip() if not pd.isna(row.get('email')) else None
        existing = session.query(Student).filter_by(email=email).first() if email else None
        if existing:
            continue
        s = Student(name=name, email=email, education=row.get('education'), semester=row.get('semester'), interests=row.get('interests'), career_goal=row.get('career_goal'))
        session.add(s)
        added += 1
    session.commit()
    return added


def load_all(app):
    from models import db as _db
    with app.app_context():
        session = _db.session
        s1 = load_skills(session)
        s2 = load_skill_relationships(session)
        s3 = load_projects(session)
        s4 = load_students(session)
        return {'skills_added': s1, 'relationships_added': s2, 'projects_added': s3, 'students_added': s4}
