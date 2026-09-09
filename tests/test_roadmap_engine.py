from app import create_app
from models import db
from models.skill import Skill, SkillRelationship
from models.project import Project
from models.student import Student
from models.skill import StudentSkill


def test_roadmap_basic_sequencing():
    """Test that roadmap respects prerequisite order."""
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()

        # Create skill chain: A -> B -> C (A prereq for B, B prereq for C)
        a = Skill(name='A')
        b = Skill(name='B')
        c = Skill(name='C')
        db.session.add_all([a, b, c])
        db.session.commit()

        # A is prereq for B
        rel1 = SkillRelationship(source_skill_id=a.id, target_skill_id=b.id, relationship_type='prerequisite')
        # B is prereq for C
        rel2 = SkillRelationship(source_skill_id=b.id, target_skill_id=c.id, relationship_type='prerequisite')
        db.session.add_all([rel1, rel2])
        db.session.commit()

        # Student is blank (no skills learned)
        st = Student(name='Alice')
        db.session.add(st)
        db.session.commit()

        from services.roadmap_engine import build_learning_roadmap

        # Request roadmap for target skill C
        roadmap = build_learning_roadmap(st, ['C'], db.session)
        
        # Validate that roadmap has stages and they're ordered correctly
        assert isinstance(roadmap, list)
        assert len(roadmap) > 0
        
        # All stages should have skills listed
        for stage in roadmap:
            assert 'stage' in stage
            assert 'skills' in stage
            assert 'estimated_weeks' in stage
            assert isinstance(stage['skills'], list)
        
        # Flatten all skills in order
        flat_skills = []
        for stage in roadmap:
            flat_skills.extend(stage['skills'])
        
        # Should contain A, B, C
        assert 'A' in flat_skills
        assert 'B' in flat_skills
        assert 'C' in flat_skills
        
        # A should come before B, B before C
        a_idx = flat_skills.index('A')
        b_idx = flat_skills.index('B')
        c_idx = flat_skills.index('C')
        assert a_idx < b_idx < c_idx, f"Expected ordering A < B < C, got indices {a_idx} < {b_idx} < {c_idx}"
