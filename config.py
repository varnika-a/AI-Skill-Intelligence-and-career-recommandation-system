import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', f'sqlite:///{BASE_DIR / "student_skills.db"}'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', str(BASE_DIR / 'uploads'))
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB
    ALLOWED_EXTENSIONS = {'pdf'}
    # Skill scoring defaults
    SKILL_WEIGHTS = {
        'self': 0.3,
        'assessment': 0.3,
        'project': 0.25,
        'resume': 0.15,
    }
    SKILL_THRESHOLDS = {
        'beginner': 25,
        'basic': 50,
        'intermediate': 70,
        'advanced': 85,
        'strong': 100,
    }
