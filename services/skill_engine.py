"""Skill scoring and aggregation engine."""
from typing import Optional, Dict
from flask import current_app


def _scale_self_report(value: float) -> Optional[float]:
    if value is None:
        return None
    # self-report expected 1-10; scale to 0-100
    try:
        v = float(value)
    except Exception:
        return None
    if 0 <= v <= 10:
        return v * 10.0
    if 0 <= v <= 100:
        return v
    return None


def compute_skill_score(self_report: Optional[float] = None,
                        assessment: Optional[float] = None,
                        project_evidence: Optional[float] = None,
                        resume_evidence: Optional[float] = None,
                        weights: Optional[Dict[str, float]] = None) -> float:
    """Combine available evidence into a 0-100 score.

    - `self_report`: 1-10 or 0-100
    - `assessment`, `project_evidence`, `resume_evidence`: 0-100
    If some sources are missing, weights are renormalized.
    """
    if weights:
        cfg_weights = weights
    else:
        try:
            cfg_weights = current_app.config.get('SKILL_WEIGHTS')
        except RuntimeError:
            cfg_weights = {'self': 0.3, 'assessment': 0.3, 'project': 0.25, 'resume': 0.15}
        if not cfg_weights:
            cfg_weights = {'self': 0.3, 'assessment': 0.3, 'project': 0.25, 'resume': 0.15}

    sources = {}
    sr = _scale_self_report(self_report)
    if sr is not None:
        sources['self'] = float(sr)
    if assessment is not None:
        sources['assessment'] = float(assessment)
    if project_evidence is not None:
        sources['project'] = float(project_evidence)
    if resume_evidence is not None:
        sources['resume'] = float(resume_evidence)

    if not sources:
        return 0.0

    total_weight = sum(cfg_weights[k] for k in sources.keys())
    score = 0.0
    for k, v in sources.items():
        score += v * (cfg_weights[k] / total_weight)

    return float(score)


def classify_score(score: float) -> str:
    try:
        thr = current_app.config.get('SKILL_THRESHOLDS')
    except RuntimeError:
        thr = None
    if not thr:
        thr = {'beginner': 25, 'basic': 50, 'intermediate': 70, 'advanced': 85, 'strong': 100}
    if score <= thr['beginner']:
        return 'Beginner'
    if score <= thr['basic']:
        return 'Basic'
    if score <= thr['intermediate']:
        return 'Intermediate'
    if score <= thr['advanced']:
        return 'Advanced'
    return 'Strong'

