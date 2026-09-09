from flask import Flask
from models import db
from routes.main import main_bp
import config
from services import data_loader


def _ensure_schema():
    """Apply small backwards-compatible upgrades for existing SQLite databases."""
    from sqlalchemy import inspect, text

    if not db.engine.url.drivername.startswith('sqlite'):
        return
    inspector = inspect(db.engine)
    upgrades = {
        'students': {
            'resume_filename': 'VARCHAR(256)',
        },
        'student_skills': {
            'self_report': 'FLOAT',
        },
    }
    for table_name, table_columns in upgrades.items():
        columns = {column['name'] for column in inspector.get_columns(table_name)}
        for column_name, column_type in table_columns.items():
            if column_name not in columns:
                db.session.execute(text(
                    f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'
                ))
        db.session.commit()


def create_app(env_config=None):
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config.Config)
    if env_config:
        app.config.update(env_config)

    db.init_app(app)

    with app.app_context():
        db.create_all()
        _ensure_schema()

    app.register_blueprint(main_bp)
    # register profile blueprint
    try:
        from routes.profile import profile_bp
        app.register_blueprint(profile_bp)
    except Exception:
        pass
    try:
        from routes.recommendations import rec_bp
        app.register_blueprint(rec_bp)
    except Exception:
        pass

    @app.cli.command('init-db')
    def init_db():
        """Initialize the database (create tables)."""
        with app.app_context():
            db.create_all()
            print('Database initialized')

    @app.cli.command('load-sample-data')
    def load_sample_data():
        """Load sample skills, relationships, projects and students from data/*.csv"""
        with app.app_context():
            db.create_all()
            res = data_loader.load_all(app)
            print('Data loaded:', res)

    @app.cli.command('evaluate-recommendations')
    def evaluate_recommendations():
        """Print recommendation counts and unlabelled quality metrics."""
        from models.student import Student
        from services.evaluation import evaluate_students

        with app.app_context():
            db.create_all()
            result = evaluate_students(Student.query.all(), db.session, k=5)
            print(result)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
