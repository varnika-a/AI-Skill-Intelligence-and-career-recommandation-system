import pytest

from app import create_app
from models import db
from models.student import Student
from models.skill import Skill, StudentSkill
from models.project import Project


@pytest.fixture
def app():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        yield app


@pytest.fixture
def client(app):
    return app.test_client()


def test_recommendation_basic(app):
    from services.recommendation_engine import recommend_projects_for_student

    # seed skills
    s1 = Skill(name='Python')
    s2 = Skill(name='Machine Learning')
    db.session.add_all([s1, s2])
    db.session.commit()

    # project requiring both
    p = Project(title='ML Web App', domain='AI', difficulty='Intermediate')
    p.required_skills.append(s1)
    p.required_skills.append(s2)
    db.session.add(p)
    db.session.commit()

    # student with Python strong, ML weak
    st = Student(name='Alice', interests='AI', career_goal='ML Engineer')
    db.session.add(st)
    db.session.commit()

    ss = StudentSkill(student_id=st.id, skill_id=s1.id, proficiency_score=85.0)
    ss2 = StudentSkill(student_id=st.id, skill_id=s2.id, proficiency_score=30.0)
    db.session.add_all([ss, ss2])
    db.session.commit()

    recs = recommend_projects_for_student(st, db.session, top_k=5)
    assert isinstance(recs, list)
    assert len(recs) == 1
    r = recs[0]
    assert r['project_id'] == p.id
    # explainability fields
    assert 'components' in r and isinstance(r['components'], dict)
    assert 'content_terms' in r and isinstance(r['content_terms'], list)
    assert 'score' in r
    assert 'Matched' in r['explanation'] or r['missing_skills']
