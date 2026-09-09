"""Skill gap detection and categorization utilities.

This module compares a student's skill scores against a target set
of skills (career or project) and returns categorized gaps:
- strong, adequate, developing, weak, missing

It also identifies missing prerequisites using SkillRelationship data.
"""
from typing import List, Dict
from flask import current_app


def analyze_student_gaps(student, target_skill_names: List[str], db_session) -> Dict:
    """Analyze gaps for `student` against `target_skill_names`.

    `db_session` should be an SQLAlchemy session (e.g., models.db.session).
    Returns a dict with categorized lists and prerequisite gaps.
    """
    # thresholds for categories
    thr = current_app.config.get('SKILL_THRESHOLDS', {'beginner': 25, 'basic': 50, 'intermediate': 70, 'advanced': 85, 'strong': 100})

    # helper to classify a score
    def _category(score: float) -> str:
        if score is None:
            return 'missing'
        if score >= 86:
            return 'strong'
        if score >= 71:
            return 'adequate'
        if score >= 51:
            return 'developing'
        if score >= 26:
            return 'weak'
        return 'missing'

    # map skill name -> Skill object
    from models.skill import Skill, StudentSkill, SkillRelationship

    name_to_skill = {s.name: s for s in db_session.query(Skill).all()}

    # get student's existing skill scores
    student_skills = {ss.skill_id: ss for ss in db_session.query(StudentSkill).filter_by(student_id=student.id).all()}

    categories = {'strong': [], 'adequate': [], 'developing': [], 'weak': [], 'missing': []}
    details = {}

    for tname in target_skill_names:
        skill = name_to_skill.get(tname)
        if not skill:
            # unknown skill name; mark as missing
            categories['missing'].append(tname)
            details[tname] = {'reason': 'unknown_skill'}
            continue

        ss = student_skills.get(skill.id)
        score = None
        if ss and ss.proficiency_score is not None and ss.proficiency_score > 0:
            score = ss.proficiency_score
        elif ss and ss.self_report is not None:
            # scale 1-10 to 0-100
            score = ss.self_report * 10.0

        cat = _category(score)
        categories[cat].append(skill.name)
        details[skill.name] = {'score': score, 'category': cat, 'evidence': ss.evidence if ss else None}

    # find prerequisite gaps: for missing skills, list prerequisites the student lacks
    prereq_gaps = {}
    missing_skills = categories['missing']
    if missing_skills:
        # query relationships where target is one of the missing skills and relationship_type=prerequisite
        targets = [name_to_skill.get(n).id for n in missing_skills if name_to_skill.get(n)]
        rels = db_session.query(SkillRelationship).filter(SkillRelationship.target_skill_id.in_(targets), SkillRelationship.relationship_type == 'prerequisite').all()
        for r in rels:
            src = db_session.query(Skill).get(r.source_skill_id)
            tgt = db_session.query(Skill).get(r.target_skill_id)
            if not src or not tgt:
                continue
            # check if student has src
            ss_src = student_skills.get(src.id)
            has_src = ss_src and ((ss_src.proficiency_score and ss_src.proficiency_score > 0) or (ss_src.self_report and ss_src.self_report > 0))
            if not has_src:
                prereq_gaps.setdefault(tgt.name, []).append(src.name)

    return {
        'categories': categories,
        'details': details,
        'prerequisite_gaps': prereq_gaps,
    }


# Backwards-compatible alias expected by older tests / callers
def detect_skill_gaps(student, target_skill_names=None, db_session=None) -> Dict:
    """Backward-compatible wrapper.

    Supports two call styles:
    - detect_skill_gaps(student_obj, target_skill_names_list, db_session)
    - detect_skill_gaps(student_dict, target_dict)  # test/legacy simple dicts
    """
    # legacy simple dict form used in tests: student and target are dicts with 'skills' lists
    if isinstance(target_skill_names, dict) and db_session is None:
        student_sk = set(student.get('skills', [])) if isinstance(student, dict) else set()
        target_sk = set(target_skill_names.get('skills', []))
        missing = list(target_sk - student_sk)
        return {'missing': missing}

    # otherwise delegate to analysis function
    return analyze_student_gaps(student, target_skill_names or [], db_session)

