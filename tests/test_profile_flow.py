import os
from app import create_app
from models import db
from models.skill import Skill
from models.student import Student


def test_profile_scoring_flow(tmp_path):
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        # create skill and student
        s = Skill(name='Python', category='Programming')
        db.session.add(s)
        db.session.commit()
        student = Student(name='Test', email='t@example.com')
        db.session.add(student)
        db.session.commit()

        client = app.test_client()
        # add self_report via form
        res = client.post(f'/profile/{student.id}/skills', data={'skill_id': s.id, 'self_report': '8'})
        assert res.status_code in (302, 303)

        # run scoring
        res2 = client.get(f'/profile/{student.id}/score')
        assert res2.status_code == 200
        body = res2.get_data(as_text=True)
        assert 'Python' in body
