from app import create_app
from models import db
from models.skill import Skill, SkillRelationship
from models.project import Project
from models.student import Student
from models.skill import StudentSkill


def test_skill_recommender_basic():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()

        # skills A -> B (A is prereq for B), and C independent
        a = Skill(name='A')
        b = Skill(name='B')
        c = Skill(name='C')
        db.session.add_all([a, b, c])
        db.session.commit()

        # relationship A -> B (prerequisite)
        rel = SkillRelationship(source_skill_id=a.id, target_skill_id=b.id, relationship_type='prerequisite')
        db.session.add(rel)
        db.session.commit()

        # project: B is required by proj1, C by proj2
        p1 = Project(title='Proj1')
        p1.required_skills.append(b)
        p2 = Project(title='Proj2')
        p2.required_skills.append(c)
        db.session.add_all([p1, p2])
        db.session.commit()

        # student knows A strongly
        st = Student(name='Bob')
        db.session.add(st)
        db.session.commit()
        ss = StudentSkill(student_id=st.id, skill_id=a.id, proficiency_score=90.0)
        db.session.add(ss)
        db.session.commit()

        from services.skill_recommender import recommend_skills_for_student

        recs = recommend_skills_for_student(st, db.session, top_k=5)
        assert isinstance(recs, list)
        # expect B recommended (has prereq A satisfied) and C recommended too
        names = [r['skill_name'] for r in recs]
        assert 'B' in names
        assert 'C' in names
        # B should rank >= C because B has project impact and prereqs satisfied
        idx_b = names.index('B')
        idx_c = names.index('C')
        assert idx_b <= idx_c
