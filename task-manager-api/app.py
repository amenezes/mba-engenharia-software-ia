import logging

from flask import Flask, jsonify
from flask_cors import CORS

from config.settings import Config
from database import db
from middlewares.error_handler import register_error_handlers
from routes.report_routes import report_bp
from routes.task_routes import task_bp
from routes.user_routes import user_bp

logging.basicConfig(level=logging.INFO)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(task_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(report_bp)

    @app.route('/health')
    def health():
        return {'status': 'ok', 'versao': '2.0.0', 'arquitetura': 'MVC'}

    @app.route('/')
    def index():
        return {'message': 'Task Manager API', 'version': '2.0', 'arquitetura': 'MVC'}

    register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app


app = create_app()


if __name__ == '__main__':
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
