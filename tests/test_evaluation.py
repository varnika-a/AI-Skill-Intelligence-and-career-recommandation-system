from app import create_app
from models import db
from models.project import Project
from models.skill import Skill, StudentSkill
from models.student import Student
from services.evaluation import evaluate_student, evaluate_students, hit_rate, precision_at_k


def test_precision_and_hit_rate_at_k():
    assert precision_at_k([1, 2, 3], {2}, 2) == 0.5
    assert hit_rate([1, 2, 3], {2}, 2) == 1.0
    assert hit_rate([1, 2, 3], {3}, 2) == 0.0
    assert precision_at_k([], {1}, 5) == 0.0


def test_evaluate_student_and_aggregate_metrics():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        db.create_all()
        python = Skill(name='Python', category='Programming')
        student = Student(name='Evaluation Student')
        db.session.add_all([python, student])
        db.session.commit()
        db.session.add(StudentSkill(student_id=student.id, skill_id=python.id, proficiency_score=90))
        project = Project(title='Python Project', domain='Programming', difficulty='Beginner')
        project.required_skills.append(python)
        db.session.add(project)
        db.session.commit()

        result = evaluate_student(
            student,
            db.session,
            relevant_project_ids=[project.id],
            relevant_skill_names=['Python'],
            k=5,
        )
        assert result['student_id'] == student.id
        assert result['project_recommendation_count'] == 1
        assert result['project_precision_at_k'] == 1.0
        assert result['project_hit_rate'] == 1.0

        aggregate = evaluate_students(
            [student],
            db.session,
            labels={student.id: {'project_ids': [project.id]}},
            k=5,
        )
        assert aggregate['student_count'] == 1
        assert aggregate['average_project_precision_at_k'] == 1.0
        assert aggregate['results'][0]['skill_precision_at_k'] == 0.0
