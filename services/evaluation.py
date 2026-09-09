"""Offline evaluation helpers for recommendation quality.

The evaluator accepts relevance labels supplied by an instructor or benchmark
rather than treating every recommendation as automatically correct.
"""
from typing import Dict, Iterable, List, Optional, Set

from services.recommendation_engine import recommend_projects_for_student
from services.skill_recommender import recommend_skills_for_student


def precision_at_k(recommended: Iterable, relevant: Iterable, k: int = 5) -> float:
    """Return the fraction of the first k recommendations that are relevant."""
    if k <= 0:
        return 0.0
    recommended_items = list(recommended)[:k]
    relevant_items = set(relevant)
    if not recommended_items:
        return 0.0
    return round(sum(item in relevant_items for item in recommended_items) / len(recommended_items), 3)


def hit_rate(recommended: Iterable, relevant: Iterable, k: int = 5) -> float:
    """Return 1 when the first k recommendations contain a relevant item."""
    if k <= 0:
        return 0.0
    return float(bool(set(list(recommended)[:k]) & set(relevant)))


def evaluate_student(student, db_session, relevant_project_ids: Optional[Iterable[int]] = None,
                     relevant_skill_names: Optional[Iterable[str]] = None, k: int = 5) -> Dict:
    """Evaluate one student's project and skill recommendations.

    Relevance labels are optional so the function can report recommendation
    counts even when a benchmark has not been annotated yet.
    """
    project_recommendations = recommend_projects_for_student(student, db_session, top_k=k)
    skill_recommendations = recommend_skills_for_student(student, db_session, top_k=k)
    project_ids = [item['project_id'] for item in project_recommendations]
    skill_names = [item['skill_name'] for item in skill_recommendations]
    relevant_projects = set(relevant_project_ids or [])
    relevant_skills = set(relevant_skill_names or [])

    return {
        'student_id': student.id,
        'k': k,
        'project_recommendation_count': len(project_ids),
        'skill_recommendation_count': len(skill_names),
        'project_precision_at_k': precision_at_k(project_ids, relevant_projects, k),
        'project_hit_rate': hit_rate(project_ids, relevant_projects, k),
        'skill_precision_at_k': precision_at_k(skill_names, relevant_skills, k),
        'skill_hit_rate': hit_rate(skill_names, relevant_skills, k),
        'project_recommendations': project_recommendations,
        'skill_recommendations': skill_recommendations,
    }


def evaluate_students(students: Iterable, db_session, labels: Optional[Dict[int, Dict]] = None,
                      k: int = 5) -> Dict:
    """Evaluate a collection of students and return per-student and averages."""
    labels = labels or {}
    results: List[Dict] = []
    for student in students:
        student_labels = labels.get(student.id, {})
        results.append(evaluate_student(
            student,
            db_session,
            relevant_project_ids=student_labels.get('project_ids', []),
            relevant_skill_names=student_labels.get('skill_names', []),
            k=k,
        ))

    def average(key: str) -> float:
        values = [result[key] for result in results]
        return round(sum(values) / len(values), 3) if values else 0.0

    return {
        'student_count': len(results),
        'k': k,
        'average_project_precision_at_k': average('project_precision_at_k'),
        'average_project_hit_rate': average('project_hit_rate'),
        'average_skill_precision_at_k': average('skill_precision_at_k'),
        'average_skill_hit_rate': average('skill_hit_rate'),
        'results': results,
    }
