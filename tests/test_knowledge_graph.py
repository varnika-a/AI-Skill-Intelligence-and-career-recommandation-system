from app import create_app
from models import db
from models.skill import Skill, SkillRelationship
from services.knowledge_graph import build_graph_from_db, get_prerequisites, get_all_prerequisites, shortest_path


def test_knowledge_graph_basic():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        # create skills
        s_python = Skill(name='Python')
        s_numpy = Skill(name='NumPy')
        s_pandas = Skill(name='Pandas')
        db.session.add_all([s_python, s_numpy, s_pandas])
        db.session.commit()

        # relationships: Python -> NumPy (prerequisite), NumPy -> Pandas (prerequisite)
        r1 = SkillRelationship(source_skill_id=s_python.id, target_skill_id=s_numpy.id, relationship_type='prerequisite', strength=1.0)
        r2 = SkillRelationship(source_skill_id=s_numpy.id, target_skill_id=s_pandas.id, relationship_type='prerequisite', strength=0.9)
        db.session.add_all([r1, r2])
        db.session.commit()

        G = build_graph_from_db(db.session)
        preds = get_prerequisites(G, 'NumPy')
        assert 'Python' in preds

        all_preds = set(get_all_prerequisites(G, 'Pandas'))
        assert 'Python' in all_preds and 'NumPy' in all_preds

        path = shortest_path(G, 'Python', 'Pandas')
        assert path == ['Python', 'NumPy', 'Pandas']
