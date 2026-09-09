from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from . import student, skill, project, assessment, recommendation  # noqa: F401
