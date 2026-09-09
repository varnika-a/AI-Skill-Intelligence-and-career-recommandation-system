import os
from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash, session
from werkzeug.utils import secure_filename
from models import db
from models.student import Student
from services.nlp_service import extract_skills_from_text
from services.skill_engine import compute_skill_score, classify_score
from services.skill_gap_engine import analyze_student_gaps

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config.get('ALLOWED_EXTENSIONS', set())


@profile_bp.route('/')
def list_profiles():
    students = Student.query.all()
    return render_template('profile_list.html', students=students)


@profile_bp.route('/create', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        education = request.form.get('education')
        semester = request.form.get('semester')
        interests = request.form.get('interests')
        career_goal = request.form.get('career_goal')

        student = Student(name=name, email=email, education=education, semester=semester, interests=interests, career_goal=career_goal)
        db.session.add(student)
        db.session.commit()
        flash('Profile created', 'success')
        return redirect(url_for('profile.view_profile', student_id=student.id))

    return render_template('profile_create.html')


@profile_bp.route('/<int:student_id>')
def view_profile(student_id):
    student = Student.query.get_or_404(student_id)
    from models.skill import Skill
    all_skills = Skill.query.order_by(Skill.name).all()
    return render_template('profile.html', student=student, all_skills=all_skills)


@profile_bp.route('/<int:student_id>/edit', methods=['GET', 'POST'])
def edit_profile(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        student.name = request.form.get('name')
        student.email = request.form.get('email')
        student.education = request.form.get('education')
        student.semester = request.form.get('semester')
        student.interests = request.form.get('interests')
        student.career_goal = request.form.get('career_goal')
        db.session.commit()
        flash('Profile updated', 'success')
        return redirect(url_for('profile.view_profile', student_id=student.id))
    return render_template('profile_edit.html', student=student)


@profile_bp.route('/<int:student_id>/upload_resume', methods=['GET', 'POST'])
def upload_resume(student_id):
    student = Student.query.get_or_404(student_id)
    if request.method == 'POST':
        if 'resume' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['resume']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER')
            os.makedirs(upload_folder, exist_ok=True)
            dest = os.path.join(upload_folder, f"{student.id}_{filename}")
            file.save(dest)
            student.resume_filename = os.path.relpath(dest, start=current_app.root_path)
            db.session.commit()

            # quick NLP extraction using controlled vocabulary
            # load vocabulary from skills table
            from models.skill import Skill
            vocab = [s.name for s in Skill.query.all()]
            text = ''
            try:
                # try simple PDF text extraction with pdfplumber
                import pdfplumber
                with pdfplumber.open(dest) as pdf:
                    for p in pdf.pages:
                        text += '\n' + p.extract_text() or ''
            except Exception:
                # fallback: read raw bytes
                try:
                    with open(dest, 'rb') as f:
                        text = f.read().decode('utf-8', errors='ignore')
                except Exception:
                    text = ''

            extracted = extract_skills_from_text(text, vocab)
            # store extracted in session for user review
            session_key = f'extracted_skills_{student.id}'
            # extracted is list of (skill, confidence) tuples
            session[session_key] = extracted

            # Do not yet persist; redirect to review page
            return redirect(url_for('profile.confirm_skills', student_id=student.id))
            # Store extracted skills as StudentSkill evidence 'resume' (moved to confirm route)
            from models.skill import Skill
            from models.skill import StudentSkill as SS
            for sk_name in extracted:
                skill_obj = Skill.query.filter_by(name=sk_name).first()
                if not skill_obj:
                    continue
                ss = SS.query.filter_by(student_id=student.id, skill_id=skill_obj.id).first()
                if not ss:
                    ss = SS(student_id=student.id, skill_id=skill_obj.id, evidence='resume')
                    db.session.add(ss)
                else:
                    # append evidence note
                    ev = ss.evidence or ''
                    if 'resume' not in ev:
                        ss.evidence = (ev + ';resume').lstrip(';')
            db.session.commit()

            # unreachable
            return redirect(url_for('profile.view_profile', student_id=student.id))
        else:
            flash('Invalid file type', 'danger')
            return redirect(request.url)

    return render_template('upload.html', student=student)


@profile_bp.route('/<int:student_id>/confirm_skills', methods=['GET', 'POST'])
def confirm_skills(student_id):
    student = Student.query.get_or_404(student_id)
    session_key = f'extracted_skills_{student.id}'
    extracted = session.get(session_key, [])
    if request.method == 'POST':
        # iterate through extracted and check which were accepted
        accepted = []
        for i in range(len(extracted)):
            if request.form.get(f'accept_{i}'):
                skill_name = request.form.get(f'skill_{i}')
                conf = float(request.form.get(f'conf_{i}', 0.0))
                accepted.append((skill_name, conf))

        # persist accepted skills
        from models.skill import Skill, StudentSkill as SS
        for name, conf in accepted:
            skill_obj = Skill.query.filter_by(name=name).first()
            if not skill_obj:
                continue
            ss = SS.query.filter_by(student_id=student.id, skill_id=skill_obj.id).first()
            if not ss:
                ss = SS(student_id=student.id, skill_id=skill_obj.id, evidence=f'resume(conf={conf:.2f})')
                db.session.add(ss)
            else:
                ev = ss.evidence or ''
                if f'resume(conf' not in ev:
                    ss.evidence = (ev + f';resume(conf={conf:.2f})').lstrip(';')
        db.session.commit()
        # clear session key
        session.pop(session_key, None)
        flash('Selected skills saved to your profile.', 'success')
        return redirect(url_for('profile.view_profile', student_id=student.id))

    return render_template('confirm_skills.html', student=student, extracted=extracted)



@profile_bp.route('/<int:student_id>/skills', methods=['POST'])
def add_skill(student_id):
    student = Student.query.get_or_404(student_id)
    skill_id = request.form.get('skill_id')
    self_report = request.form.get('self_report')
    if not skill_id:
        flash('No skill selected', 'danger')
        return redirect(url_for('profile.view_profile', student_id=student.id))
    from models.skill import Skill, StudentSkill as SS
    skill = Skill.query.get(int(skill_id))
    if not skill:
        flash('Invalid skill', 'danger')
        return redirect(url_for('profile.view_profile', student_id=student.id))
    ss = SS.query.filter_by(student_id=student.id, skill_id=skill.id).first()
    if not ss:
        ss = SS(student_id=student.id, skill_id=skill.id)
        db.session.add(ss)
    # store self_report if provided
    if self_report:
        try:
            v = float(self_report)
            if 0 <= v <= 10:
                ss.self_report = v
            else:
                ss.self_report = max(0.0, min(10.0, v))
        except Exception:
            pass
    db.session.commit()
    flash('Skill updated', 'success')
    return redirect(url_for('profile.view_profile', student_id=student.id))


@profile_bp.route('/<int:student_id>/delete', methods=['POST'])
def delete_profile(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Profile deleted', 'info')
    return redirect(url_for('profile.list_profiles'))



@profile_bp.route('/<int:student_id>/score')
def score_profile(student_id):
    student = Student.query.get_or_404(student_id)
    # gather candidate skills from student_skills and assessments
    from models.skill import Skill, StudentSkill as SS
    from models.assessment import Assessment

    candidate_skill_ids = set()
    for ss in SS.query.filter_by(student_id=student.id).all():
        candidate_skill_ids.add(ss.skill_id)
    for a in Assessment.query.filter_by(student_id=student.id).all():
        candidate_skill_ids.add(a.skill_id)

    results = []
    for sid in candidate_skill_ids:
        skill = Skill.query.get(sid)
        ss = SS.query.filter_by(student_id=student.id, skill_id=sid).first()
        # self report
        self_report = None
        if ss and ss.self_report is not None:
            self_report = ss.self_report

        # assessment average
        assessments = Assessment.query.filter_by(student_id=student.id, skill_id=sid).all()
        assessment_score = None
        if assessments:
            assessment_score = sum(a.score for a in assessments) / len(assessments)

        # resume evidence
        resume_evidence = None
        if ss and ss.evidence and 'resume' in ss.evidence:
            resume_evidence = 65.0

        # project evidence: TODO in Phase 8
        project_evidence = None

        final = compute_skill_score(self_report=self_report, assessment=assessment_score, project_evidence=project_evidence, resume_evidence=resume_evidence)

        # persist computed score into StudentSkill (proficiency_score 0-100)
        if not ss:
            ss = SS(student_id=student.id, skill_id=skill.id, proficiency_score=final, evidence='computed')
            db.session.add(ss)
        else:
            ss.proficiency_score = final
            ss.evidence = (ss.evidence or '') + ';computed'
        results.append({'skill': skill.name, 'score': final, 'classification': classify_score(final)})

    db.session.commit()
    return render_template('profile_scores.html', student=student, results=results)


@profile_bp.route('/<int:student_id>/gaps')
def view_gaps(student_id):
    student = Student.query.get_or_404(student_id)
    # allow optional project_id parameter to compare against a project
    project_id = request.args.get('project_id', type=int)
    from models.project import Project
    target_skills = []
    if project_id:
        proj = Project.query.get(project_id)
        if proj:
            target_skills = [s.name for s in proj.required_skills]
    else:
        # try career goal mapping (simple keyword match)
        career_map = {
            'NLP Engineer': ['Python', 'Machine Learning', 'NLP', 'TF-IDF', 'Transformers'],
            'Data Scientist': ['Python', 'Pandas', 'Statistics', 'Machine Learning', 'Data Visualization'],
            'Web Developer': ['HTML', 'CSS', 'JavaScript', 'Flask', 'SQL'],
        }
        cg = (student.career_goal or '').strip()
        target_skills = career_map.get(cg, [])

    from models import db as _db
    analysis = analyze_student_gaps(student, target_skills, _db.session)
    return render_template('profile_gaps.html', student=student, analysis=analysis, target_skills=target_skills)
