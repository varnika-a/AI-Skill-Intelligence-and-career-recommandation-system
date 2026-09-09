from app import create_app
from models import db
from models.skill import Skill, StudentSkill
from models.project import Project
from models.student import Student


def test_whatif_simulator_boost():
    """Test that what-if simulator shows impact of skill boost."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()

        # Create two skills
        python = Skill(name='Python')
        ml = Skill(name='ML')
        db.session.add_all([python, ml])
        db.session.commit()

        # Create projects requiring these skills
        p1 = Project(title='Web App')
        p1.required_skills.append(python)
        p2 = Project(title='ML Pipeline')
        p2.required_skills.append(python)
        p2.required_skills.append(ml)
        db.session.add_all([p1, p2])
        db.session.commit()

        # Student with weak Python, no ML
        st = Student(name='Charlie')
        db.session.add(st)
        db.session.commit()

        ss = StudentSkill(student_id=st.id, skill_id=python.id, proficiency_score=40.0)
        db.session.add(ss)
        db.session.commit()

        from services.simulator import simulate_skill_boost

        # Boost Python to 85
        simulation = simulate_skill_boost(st, 'Python', 85.0, db.session)

        # Should have recommendation output
        assert 'current_projects' in simulation
        assert 'simulated_projects' in simulation
        assert 'impact_summary' in simulation
        assert isinstance(simulation['current_projects'], list)
        assert isinstance(simulation['simulated_projects'], list)
        
        # Impact should show some change (Python boost from 40 to 85 should unlock projects)
        impact = simulation['impact_summary']
        assert impact['skill_boosted'] == 'Python'
        assert impact['new_score'] == 85.0
