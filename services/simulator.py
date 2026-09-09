"""What-if simulator for analyzing impact of hypothetical skill changes.

Allows users to explore how boosting a skill would affect:
- Project recommendations
- Skill recommendations
- Learning roadmap
"""
from typing import List, Dict, Tuple
from copy import deepcopy


def simulate_skill_boost(student, skill_name: str, new_score: float, db_session) -> Dict:
    """Simulate the impact of boosting a skill to a target score.

    Returns a dict with:
    - current_projects: current project recommendations
    - simulated_projects: project recommendations with boosted skill
    - current_skills: current skill recommendations
    - simulated_skills: skill recommendations with boosted skill
    - impact_summary: summary of changes
    """
    from models.skill import Skill, StudentSkill
    from services.recommendation_engine import recommend_projects_for_student
    from services.skill_recommender import recommend_skills_for_student

    # get current recommendations
    current_projects = recommend_projects_for_student(student, db_session, top_k=5)
    current_skills = recommend_skills_for_student(student, db_session, top_k=10)

    # create a hypothetical student copy by modifying skill scores in memory
    # (we won't actually save to DB)
    from models.student import Student as StudentModel

    hypothetical = StudentModel(
        name=student.name,
        email=student.email,
        education=student.education,
        semester=student.semester,
        interests=student.interests,
        career_goal=student.career_goal,
    )
    hypothetical.id = student.id  # use same ID for query matching

    # copy existing student skills
    for ss in student.skills:
        new_ss = StudentSkill()
        new_ss.student_id = hypothetical.id
        new_ss.skill_id = ss.skill_id
        new_ss.proficiency_score = ss.proficiency_score
        new_ss.self_report = ss.self_report
        new_ss.evidence = ss.evidence
        hypothetical.skills.append(new_ss)

    # boost the target skill or add it
    skill_obj = db_session.query(Skill).filter_by(name=skill_name).first()
    if not skill_obj:
        return {
            'error': f'Skill "{skill_name}" not found',
            'current_projects': current_projects,
            'current_skills': current_skills,
        }

    found = False
    for ss in hypothetical.skills:
        if ss.skill_id == skill_obj.id:
            ss.proficiency_score = new_score
            found = True
            break

    if not found:
        new_ss = StudentSkill()
        new_ss.student_id = hypothetical.id
        new_ss.skill_id = skill_obj.id
        new_ss.proficiency_score = new_score
        hypothetical.skills.append(new_ss)

    # get simulated recommendations
    simulated_projects = recommend_projects_for_student(hypothetical, db_session, top_k=5)
    simulated_skills = recommend_skills_for_student(hypothetical, db_session, top_k=10)

    # calculate impact
    current_proj_ids = {p['project_id'] for p in current_projects}
    simulated_proj_ids = {p['project_id'] for p in simulated_projects}
    new_projects = simulated_proj_ids - current_proj_ids
    lost_projects = current_proj_ids - simulated_proj_ids

    current_skill_names = {s['skill_name'] for s in current_skills}
    simulated_skill_names = {s['skill_name'] for s in simulated_skills}
    new_skills = simulated_skill_names - current_skill_names
    lost_skills = current_skill_names - simulated_skill_names

    impact_summary = {
        'skill_boosted': skill_name,
        'new_score': new_score,
        'new_projects_count': len(new_projects),
        'lost_projects_count': len(lost_projects),
        'new_skills_count': len(new_skills),
        'lost_skills_count': len(lost_skills),
        'new_projects': list(new_projects)[:3],  # top 3 samples
        'new_skills': list(new_skills)[:3],
    }

    return {
        'current_projects': current_projects,
        'simulated_projects': simulated_projects,
        'current_skills': current_skills,
        'simulated_skills': simulated_skills,
        'impact_summary': impact_summary,
    }


def simulate_skill_change(student_profile, skill_name, new_value):
    """Legacy alias for backwards compatibility."""
    profile = dict(student_profile)
    skills = profile.get('skills', {})
    skills[skill_name] = new_value
    profile['skills'] = skills
    return profile

