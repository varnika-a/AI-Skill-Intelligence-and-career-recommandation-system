from app import create_app
from models import db
from models.student import Student
from models.skill import Skill
from models.assessment import Assessment
from datetime import datetime, timedelta


def test_skill_evolution_history():
    """Test that skill evolution tracker captures assessment history."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()

        # Create skill and student
        python = Skill(name='Python')
        db.session.add(python)
        db.session.commit()

        st = Student(name='Dave')
        db.session.add(st)
        db.session.commit()

        # Record multiple assessments over time
        base_date = datetime.utcnow()
        for i, score in enumerate([30, 40, 55, 65, 75]):
            a = Assessment(
                student_id=st.id,
                skill_id=python.id,
                score=float(score),
                date=base_date + timedelta(days=i*7)
            )
            db.session.add(a)
        db.session.commit()

        from services.skill_evolution_tracker import get_skill_history

        hist = get_skill_history(st, 'Python', db.session)

        assert hist['skill_name'] == 'Python'
        assert hist['current_score'] == 75
        assert hist['initial_score'] == 30
        assert hist['improvement'] == 45.0
        assert hist['avg_score'] == 53.0
        assert hist['trend'] == 'improving'
        assert hist['assessment_count'] == 5
        assert hist['velocity_weeks'] > 0  # should show weeks to level 80
        assert len(hist['assessments']) == 5


def test_skill_evolution_record_assessment():
    """Test recording a new assessment."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()

        skill = Skill(name='JavaScript')
        db.session.add(skill)
        db.session.commit()

        st = Student(name='Eve')
        db.session.add(st)
        db.session.commit()

        from services.skill_evolution_tracker import record_assessment

        # Record valid assessment
        error = record_assessment(st, 'JavaScript', 60.0, db.session)
        assert error is None

        # Check it was saved
        a = db.session.query(Assessment).filter_by(student_id=st.id, skill_id=skill.id).first()
        assert a is not None
        assert a.score == 60.0

        # Try invalid score
        error = record_assessment(st, 'JavaScript', 150, db.session)
        assert error is not None
        assert '0 and 100' in error

        # Try nonexistent skill
        error = record_assessment(st, 'Rust', 75, db.session)
        assert error is not None
        assert 'not found' in error
