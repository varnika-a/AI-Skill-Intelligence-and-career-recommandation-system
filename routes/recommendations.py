from flask import Blueprint, render_template, request
from models import db
from services.recommendation_engine import recommend_projects_for_student
from models.student import Student
from services.skill_recommender import recommend_skills_for_student
from services.roadmap_engine import build_learning_roadmap
from services.simulator import simulate_skill_boost
from services.skill_evolution_tracker import get_all_skill_histories

rec_bp = Blueprint('recommendations', __name__, url_prefix='/recommendations')


@rec_bp.route('/student/<int:student_id>')
def student_recommendations(student_id):
    student = Student.query.get_or_404(student_id)
    recs = recommend_projects_for_student(student, db.session, top_k=10)
    return render_template('recommendations.html', student=student, recommendations=recs)


@rec_bp.route('/student/<int:student_id>/skills')
def student_skill_recommendations(student_id):
    student = Student.query.get_or_404(student_id)
    recs = recommend_skills_for_student(student, db.session, top_k=20)
    return render_template('skill_recommendations.html', student=student, recommendations=recs)


@rec_bp.route('/student/<int:student_id>/roadmap')
def student_roadmap(student_id):
    student = Student.query.get_or_404(student_id)
    # Get top recommended skills
    recs = recommend_skills_for_student(student, db.session, top_k=10)
    target_skills = [r['skill_name'] for r in recs]
    roadmap = build_learning_roadmap(student, target_skills, db.session)
    return render_template('roadmap.html', student=student, roadmap=roadmap)


@rec_bp.route('/student/<int:student_id>/whatif', methods=['GET', 'POST'])
def student_whatif(student_id):
    student = Student.query.get_or_404(student_id)
    from models.skill import Skill
    all_skills = db.session.query(Skill).all()
    
    simulation = None
    if request.method == 'POST':
        skill_name = request.form.get('skill_name')
        try:
            new_score = float(request.form.get('new_score', 75))
        except (TypeError, ValueError):
            new_score = 75.0
        new_score = max(0, min(100, new_score))  # clamp 0-100
        simulation = simulate_skill_boost(student, skill_name, new_score, db.session)
    
    return render_template('whatif_simulator.html', student=student, all_skills=all_skills, simulation=simulation)


@rec_bp.route('/student/<int:student_id>/evolution', methods=['GET', 'POST'])
def student_evolution(student_id):
    from services.skill_evolution_tracker import get_all_skill_histories, record_assessment
    from models.skill import Skill
    
    student = Student.query.get_or_404(student_id)
    all_skills = db.session.query(Skill).all()
    error = None
    
    if request.method == 'POST':
        skill_name = request.form.get('skill_name')
        try:
            new_score = float(request.form.get('new_score', 50))
        except (TypeError, ValueError):
            new_score = 50.0
        new_score = max(0, min(100, new_score))  # clamp 0-100
        error = record_assessment(student, skill_name, new_score, db.session)
    
    histories = get_all_skill_histories(student, db.session, limit=20)
    return render_template('skill_evolution.html', student=student, all_skills=all_skills, histories=histories, error=error)


@rec_bp.route('/student/<int:student_id>/dashboard')
def student_dashboard(student_id):
    from models.assessment import Assessment
    from models.project import Project

    student = Student.query.get_or_404(student_id)
    project_recommendations = recommend_projects_for_student(student, db.session, top_k=5)
    skill_recommendations = recommend_skills_for_student(student, db.session, top_k=5)
    histories = get_all_skill_histories(student, db.session, limit=20)

    skill_labels = [student_skill.skill.name for student_skill in student.skills]
    skill_scores = [student_skill.proficiency_score or 0 for student_skill in student.skills]
    average_score = round(sum(skill_scores) / len(skill_scores), 1) if skill_scores else 0
    assessment_count = db.session.query(Assessment).filter_by(student_id=student.id).count()

    dashboard = {
        'skill_count': len(student.skills),
        'average_score': average_score,
        'assessment_count': assessment_count,
        'project_count': db.session.query(Project).count(),
        'skill_labels': skill_labels,
        'skill_scores': skill_scores,
        'project_recommendations': project_recommendations,
        'skill_recommendations': skill_recommendations,
        'histories': histories,
    }
    return render_template('dashboard.html', student=student, dashboard=dashboard)

