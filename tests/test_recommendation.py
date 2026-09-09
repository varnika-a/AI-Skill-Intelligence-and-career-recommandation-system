from services.recommendation_engine import recommend_projects_for_student


def test_recommendation_stub():
    projects = ['p1', 'p2', 'p3']
    rec = recommend_projects_for_student({}, projects, top_k=2)
    assert len(rec) == 2
