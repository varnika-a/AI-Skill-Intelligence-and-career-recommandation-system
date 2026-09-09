"""Skill evolution tracker: analyze assessment history over time.

Tracks how student skill scores progress, calculates learning velocity,
and identifies skill improvement patterns.
"""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models.assessment import Assessment
from models.skill import Skill


def get_skill_history(student, skill_name: str, db_session) -> Dict:
    """Get assessment history for a specific skill.

    Returns dict with:
    - skill_name: str
    - assessments: list of {date, score} sorted chronologically
    - current_score: float (latest)
    - improvement: float (latest - oldest)
    - avg_score: float
    - trend: 'improving'|'declining'|'stable'
    - velocity: float (weeks to next level, or -1 if declining)
    """
    skill = db_session.query(Skill).filter_by(name=skill_name).first()
    if not skill:
        return {'error': f'Skill "{skill_name}" not found'}

    # Query all assessments for this student-skill pair
    assessments = (
        db_session.query(Assessment)
        .filter_by(student_id=student.id, skill_id=skill.id)
        .order_by(Assessment.date.asc())
        .all()
    )

    if not assessments:
        return {'error': f'No assessment history for {skill_name}'}

    # Extract scores and dates
    history = [{'date': a.date.isoformat(), 'score': a.score} for a in assessments]
    scores = [a.score for a in assessments]
    current = scores[-1]
    initial = scores[0]
    improvement = current - initial

    # Calculate trend
    if len(scores) >= 2:
        recent_change = scores[-1] - scores[-2]
        trend = 'improving' if recent_change > 2 else ('declining' if recent_change < -2 else 'stable')
    else:
        trend = 'stable'

    # Calculate velocity (weeks to reach 80 if improving linearly)
    velocity = -1
    if trend == 'improving' and current < 80:
        days_span = (assessments[-1].date - assessments[0].date).days
        if days_span > 0:
            rate = (current - initial) / days_span  # points per day
            if rate > 0:
                days_to_80 = (80 - current) / rate
                velocity = round(days_to_80 / 7, 1)  # convert to weeks

    return {
        'skill_name': skill_name,
        'assessments': history,
        'current_score': current,
        'initial_score': initial,
        'improvement': round(improvement, 2),
        'avg_score': round(sum(scores) / len(scores), 2),
        'trend': trend,
        'velocity_weeks': velocity,
        'assessment_count': len(assessments),
    }


def get_all_skill_histories(student, db_session, limit: int = 10) -> List[Dict]:
    """Get evolution summary for all skills the student has been assessed on.

    Returns list of dicts (same format as get_skill_history).
    Sorted by most recent assessment.
    """
    # Get all unique skills with assessments
    skill_ids = (
        db_session.query(Assessment.skill_id)
        .filter_by(student_id=student.id)
        .distinct()
        .all()
    )

    histories = []
    for (skill_id,) in skill_ids:
        skill = db_session.query(Skill).get(skill_id)
        if skill:
            hist = get_skill_history(student, skill.name, db_session)
            if 'error' not in hist:
                histories.append(hist)

    # Sort by most recent assessment date
    histories.sort(
        key=lambda h: max(
            (a['date'] for a in h['assessments']), default=datetime.utcnow().isoformat()
        ),
        reverse=True,
    )

    return histories[:limit]


def record_assessment(student, skill_name: str, score: float, db_session) -> Optional[str]:
    """Record a new assessment for a student skill.

    Returns error message if any, else None (success).
    """
    if not (0 <= score <= 100):
        return 'Score must be between 0 and 100'

    skill = db_session.query(Skill).filter_by(name=skill_name).first()
    if not skill:
        return f'Skill "{skill_name}" not found'

    assessment = Assessment(student_id=student.id, skill_id=skill.id, score=score)
    db_session.add(assessment)
    db_session.commit()
    return None
