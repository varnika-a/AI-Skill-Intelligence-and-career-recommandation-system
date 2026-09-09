"""Skill recommendation engine using gap analysis and the knowledge graph.

Provides `recommend_skills_for_student(student, db_session, top_k=10)` which
returns ranked skill suggestions with explanations.
"""
from typing import List, Dict


def recommend_skills_for_student(student, db_session, top_k: int = 10) -> List[Dict]:
    from models.skill import Skill
    from models.project import Project
    from services.skill_gap_engine import analyze_student_gaps
    from services.knowledge_graph import build_graph_from_db, get_prerequisites

    # collect all skills
    skills = db_session.query(Skill).all()
    skill_names = [s.name for s in skills]

    # analyze student gaps across all skills
    gaps = analyze_student_gaps(student, skill_names, db_session)
    categories = gaps.get('categories', {})
    details = gaps.get('details', {})

    # weights for categories (higher => more recommended)
    cat_weight = {'missing': 1.0, 'weak': 0.8, 'developing': 0.6, 'adequate': 0.3, 'strong': 0.0}

    # build knowledge graph
    G = build_graph_from_db(db_session)

    # project impact: count projects requiring each skill
    proj_counts = {}
    max_proj = 1
    for s in skills:
        cnt = len(s.projects)
        proj_counts[s.name] = cnt
        if cnt > max_proj:
            max_proj = cnt

    recommendations = []
    # student strong/adequate skills set
    strong_set = set(categories.get('strong', []) + categories.get('adequate', []))

    for s in skills:
        name = s.name
        cat = details.get(name, {}).get('category', 'missing')
        base = cat_weight.get(cat, 0.0)

        # prerequisites missing count
        prereqs = get_prerequisites(G, name)
        prereq_missing = 0
        for p in prereqs:
            if p not in strong_set:
                prereq_missing += 1

        # project impact normalized
        impact = proj_counts.get(name, 0) / max_proj if max_proj > 0 else 0.0

        # score: prefer high base, fewer missing prereqs, higher impact
        score = base * (1.0 / (1 + prereq_missing)) + 0.2 * impact

        explanation = f"category={cat}; prereq_missing={prereq_missing}; projects={proj_counts.get(name,0)}"

        recommendations.append({
            'skill_name': name,
            'score': float(round(score * 100, 2)),
            'category': cat,
            'prereq_missing': prereq_missing,
            'project_count': proj_counts.get(name, 0),
            'explanation': explanation,
        })

    recommendations.sort(key=lambda x: x['score'], reverse=True)
    # filter out skills with zero score
    recommendations = [r for r in recommendations if r['score'] > 0][:top_k]
    return recommendations
