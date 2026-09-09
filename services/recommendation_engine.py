"""Content-based project recommendation engine with TF-IDF and cosine similarity.

If scikit-learn is unavailable, falls back to a heuristic-based scorer.
"""
from typing import List, Dict
from math import isfinite


def _difficulty_value(difficulty: str) -> int:
    mapping = {'beginner': 0, 'intermediate': 1, 'advanced': 2}
    return mapping.get((difficulty or '').strip().lower(), 1)


def _fallback_score(student, db_session, project):
    # keep previous simple heuristic as fallback
    from models.skill import StudentSkill
    ss_rows = db_session.query(StudentSkill).filter_by(student_id=student.id).all()
    skill_scores = { (ss.skill.name if ss.skill else ''): (ss.proficiency_score or (ss.self_report or 0) * 10.0) for ss in ss_rows }
    required = [s.name for s in project.required_skills]
    matched = [r for r in required if skill_scores.get(r, 0) >= 50]
    matched_scores = [skill_scores.get(r, 0) for r in matched]
    matched_score_component = sum(matched_scores) / (len(required) * 100) if required else 0.0
    missing = [r for r in required if r not in matched]
    gap_penalty = len(missing) / len(required) if required else 1.0
    score = (0.6 * matched_score_component + 0.4 * (1 - gap_penalty))
    return float(max(0.0, min(1.0, score)) * 100.0), matched, missing


def recommend_projects_for_student(student, db_session, top_k: int = 5) -> List[Dict]:
    """Return top_k project recommendations with explanations."""
    # Backwards compatibility: some callers/tests pass a list of projects
    # as the second argument. Detect that and handle simply.
    if isinstance(db_session, (list, tuple)):
        projects_list = list(db_session)
        # legacy behavior: return first top_k items
        return [{'project_id': None, 'title': p, 'score': 0.0} for p in projects_list[:top_k]]
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity
        sklearn_ok = True
    except Exception:
        sklearn_ok = False

    from models.project import Project
    from models.skill import StudentSkill

    projects = db_session.query(Project).all()

    # Build student text profile from skills, interests, career_goal
    ss_rows = db_session.query(StudentSkill).filter_by(student_id=student.id).all()
    student_skills = []
    skill_scores = {}
    for ss in ss_rows:
        name = ss.skill.name if ss.skill else None
        if name:
            student_skills.append(name)
            score = ss.proficiency_score if (ss.proficiency_score is not None) else ((ss.self_report or 0) * 10.0)
            skill_scores[name] = float(score or 0.0)

    student_text = ' '.join(student_skills + [student.interests or '', student.career_goal or ''])

    recommendations = []

    if sklearn_ok and projects:
        # Prepare corpus of project texts
        proj_texts = []
        proj_map = []
        for p in projects:
            skills = ' '.join([s.name for s in p.required_skills])
            gained = ' '.join([s.strip() for s in (getattr(p, 'skills_gained', '') or '').split(',') if s.strip()])
            text = ' '.join([p.title or '', p.description or '', p.domain or '', skills, gained])
            proj_texts.append(text)
            proj_map.append(p)

        vectorizer = TfidfVectorizer(stop_words='english')
        X = vectorizer.fit_transform(proj_texts)
        s_vec = vectorizer.transform([student_text])

        sims = cosine_similarity(s_vec, X)[0]  # array of similarities

        for idx, p in enumerate(proj_map):
            content_sim = float(sims[idx]) if isfinite(sims[idx]) else 0.0

            # skill match component
            required = [s.name for s in p.required_skills]
            matched = [r for r in required if skill_scores.get(r, 0) >= 50]
            matched_scores = [skill_scores.get(r, 0) for r in matched]
            matched_comp = sum(matched_scores) / (len(required) * 100) if required else 0.0
            missing = [r for r in required if r not in matched]

            # interest/career alignment
            interests = (student.interests or '').lower()
            career = (student.career_goal or '').lower()
            interest_score = 1.0 if (p.domain and (p.domain.lower() in interests or p.domain.lower() in career)) else 0.0

            # potential growth
            gained_list = [s.strip() for s in (getattr(p, 'skills_gained', '') or '').split(',') if s.strip()]
            potential = sum(1 for g in gained_list if skill_scores.get(g, 0) < 60)
            potential_score = potential / max(1, len(gained_list)) if gained_list else 0.0

            # combine weights: content 0.5, skill match 0.25, gap penalty 0.1, interest 0.1, potential 0.05
            gap_penalty = len(missing) / len(required) if required else 1.0
            score = (0.5 * content_sim + 0.25 * matched_comp + 0.1 * (1 - gap_penalty) + 0.1 * interest_score + 0.05 * potential_score)
            score = max(0.0, min(1.0, score)) * 100.0

            # extract top contributing TF-IDF terms (feature-level explainability)
            content_terms = []
            try:
                feat_names = vectorizer.get_feature_names_out()
                p_vec = X[idx].toarray()[0]
                s_vec_arr = s_vec.toarray()[0]
                contrib = s_vec_arr * p_vec
                top_idx = contrib.argsort()[-5:][::-1]
                content_terms = [feat_names[i] for i in top_idx if contrib[i] > 0]
            except Exception:
                content_terms = []

            explanation = []
            explanation.append(f"Content similarity: {content_sim:.2f}")
            explanation.append(f"Matched {len(matched)}/{len(required)} required skills")
            if missing:
                explanation.append(f"Missing: {', '.join(missing)}")
            if interest_score > 0:
                explanation.append(f"Matches interest/career: {p.domain}")
            if potential_score > 0:
                explanation.append(f"Grows skills: {', '.join(gained_list)}")

            components = {
                'content_similarity': float(round(content_sim, 4)),
                'skill_match': float(round(matched_comp, 4)),
                'gap_penalty': float(round(gap_penalty, 4)),
                'interest': float(round(interest_score, 4)),
                'potential': float(round(potential_score, 4)),
            }

            recommendations.append({
                'project_id': p.id,
                'title': p.title,
                'domain': p.domain,
                'difficulty': p.difficulty,
                'score': float(score),
                'matched_skills': matched,
                'missing_skills': missing,
                'skills_gained': gained_list,
                'explanation': '; '.join(explanation),
                'components': components,
                'content_terms': content_terms,
            })

    else:
        # fallback: heuristic per-project
        for p in projects:
            try:
                score, matched, missing = _fallback_score(student, db_session, p)
            except Exception:
                score = 0.0
                matched = []
                missing = []
            recommendations.append({
                'project_id': p.id,
                'title': p.title,
                'domain': p.domain,
                'difficulty': p.difficulty,
                'score': float(score),
                'matched_skills': matched,
                'missing_skills': missing,
                'skills_gained': [s.strip() for s in (getattr(p, 'skills_gained', '') or '').split(',') if s.strip()],
                'explanation': 'Fallback heuristic'
            })

    recommendations.sort(key=lambda x: x['score'], reverse=True)
    return recommendations[:top_k]

