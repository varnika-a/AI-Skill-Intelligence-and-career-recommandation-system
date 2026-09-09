from services.skill_gap_engine import detect_skill_gaps


def test_skill_gap_detect():
    student = {'skills': ['Python', 'Pandas']}
    target = {'skills': ['Python', 'NLP']}
    gaps = detect_skill_gaps(student, target)
    assert 'NLP' in gaps['missing']
