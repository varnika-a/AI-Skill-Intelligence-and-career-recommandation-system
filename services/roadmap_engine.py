"""Learning roadmap engine using topological sorting of skills.

Given a student and a set of target skills, builds a personalized learning
roadmap that respects prerequisites and estimates time/effort per stage.
"""
from typing import List, Dict
import networkx as nx


def build_learning_roadmap(student, target_skill_names: List[str], db_session) -> List[Dict]:
    """Build a sequenced learning roadmap for target skills, respecting prerequisites.

    Returns a list of "stages" where each stage is a set of skills that can be
    learned in parallel (no dependency conflicts), ordered by prerequisite depth.
    """
    from models.skill import Skill, StudentSkill
    from services.knowledge_graph import build_graph_from_db, get_prerequisites
    from services.skill_gap_engine import analyze_student_gaps

    # get student's current skill scores
    student_skills = {}
    ss_rows = db_session.query(StudentSkill).filter_by(student_id=student.id).all()
    for ss in ss_rows:
        if ss.skill:
            score = ss.proficiency_score if (ss.proficiency_score is not None) else ((ss.self_report or 0) * 10.0)
            student_skills[ss.skill.name] = float(score or 0.0)

    # build knowledge graph
    G = build_graph_from_db(db_session)

    # collect all skills needed: targets + their prerequisites (transitive)
    needed_skills = set(target_skill_names)
    to_explore = list(target_skill_names)
    while to_explore:
        skill = to_explore.pop(0)
        prereqs = get_prerequisites(G, skill)
        for p in prereqs:
            if p not in needed_skills:
                needed_skills.add(p)
                to_explore.append(p)

    # build subgraph with only needed skills
    subgraph = G.subgraph(needed_skills).copy()

    # topological sort: this gives us an order respecting prerequisites
    try:
        topo_order = list(nx.topological_sort(subgraph))
    except nx.NetworkXError:
        # cycle detected; fallback to arbitrary order
        topo_order = list(needed_skills)

    # group skills into stages (levels)
    # stage i contains skills whose prerequisites are in stages 0..i-1
    stages = []
    learned = set(target_skill_names)  # assume targets are acceptable end-goals even if not learned
    placed = set()

    for skill in topo_order:
        prereqs = set(get_prerequisites(subgraph, skill))
        # can place this skill if all prereqs are already placed or student knows them
        if prereqs.issubset(placed) or all(p in student_skills and student_skills.get(p, 0) >= 50 for p in prereqs):
            if not stages or len(stages[-1]) >= 3:
                # start a new stage if current one is full (up to 3 skills per stage)
                stages.append([])
            stages[-1].append(skill)
            placed.add(skill)

    # if any skills couldn't be placed (shouldn't happen with good data), add them to final stage
    unplaced = needed_skills - placed
    if unplaced:
        if stages:
            stages[-1].extend(list(unplaced))
        else:
            stages.append(list(unplaced))

    # build roadmap with explanations
    roadmap = []
    stage_num = 1
    for stage_skills in stages:
        # estimate effort for this stage (average skill difficulty + prereq count)
        effort_scores = []
        for sn in stage_skills:
            prereqs = get_prerequisites(subgraph, sn)
            current_score = student_skills.get(sn, 0.0)
            # effort = (100 - current_score) / 10 + len(prereqs) * 2
            effort = (100.0 - current_score) / 10.0 + len(prereqs) * 0.5
            effort_scores.append(effort)

        avg_effort = sum(effort_scores) / len(effort_scores) if effort_scores else 5.0
        weeks = max(1, int(avg_effort / 2))  # estimate weeks (rough)

        explanations = []
        for sn in stage_skills:
            prereqs = get_prerequisites(subgraph, sn)
            current = student_skills.get(sn, 0.0)
            status = "New" if sn not in student_skills else f"Level {int(current/20)}"
            prereq_str = f" (requires: {', '.join(prereqs)})" if prereqs else ""
            explanations.append(f"{sn}: {status}{prereq_str}")

        roadmap.append({
            'stage': stage_num,
            'skills': stage_skills,
            'estimated_weeks': weeks,
            'explanation': '; '.join(explanations),
        })
        stage_num += 1

    return roadmap


def generate_roadmap(skills, knowledge_graph=None, max_steps=10):
    """Legacy alias for backwards compatibility."""
    roadmap = []
    for s in skills[:max_steps]:
        roadmap.append({'skill': s, 'why': 'Placeholder reason', 'target_level': 'Intermediate'})
    return roadmap
