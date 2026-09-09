from app import create_app
from models import db
from models.skill import Skill, StudentSkill
from models.student import Student


def test_analyze_student_gaps():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        # create skills
        s1 = Skill(name='Python')
        s2 = Skill(name='NLP')
        db.session.add_all([s1, s2])
        db.session.commit()
        student = Student(name='Gap Tester')
        db.session.add(student)
        db.session.commit()
        # student has Python self-report 8
        ss = StudentSkill(student_id=student.id, skill_id=s1.id, self_report=8)
        db.session.add(ss)
        db.session.commit()

        from services.skill_gap_engine import analyze_student_gaps
        analysis = analyze_student_gaps(student, ['Python', 'NLP'], db.session)
        assert 'Python' in analysis['categories']['strong'] or 'Python' in analysis['categories']['adequate'] or 'Python' in analysis['categories']['developing']
        assert 'NLP' in analysis['categories']['missing']
