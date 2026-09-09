from app import create_app
from models import db
from models.student import Student
from models.skill import Skill, StudentSkill
from models.assessment import Assessment


def test_student_dashboard_displays_aggregates():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        skill = Skill(name='Python', category='Programming')
        student = Student(name='Dashboard Student')
        db.session.add_all([skill, student])
        db.session.commit()
        db.session.add(StudentSkill(student_id=student.id, skill_id=skill.id, proficiency_score=80))
        db.session.add(Assessment(student_id=student.id, skill_id=skill.id, score=80))
        db.session.commit()

        response = app.test_client().get(f'/recommendations/student/{student.id}/dashboard')

        assert response.status_code == 200
        assert b'Dashboard Student' in response.data
        assert b'Tracked skills' in response.data
        assert b'Average proficiency' in response.data
        assert b'Current skill profile' in response.data
        assert b'Python' in response.data
