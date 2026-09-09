from services.skill_engine import compute_skill_score


def test_compute_skill_score_basic():
    score = compute_skill_score(self_report=80, assessment=70, project_evidence=60, resume_evidence=50)
    assert 0 <= score <= 100
