import logging

from flask import Flask, send_from_directory
from flask_cors import CORS

from config.settings import Config
from database import get_db
from middlewares.error_handler import register_error_handlers
from routes import register_routes

logging.basicConfig(level=logging.INFO)


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, origins=["*"])

    get_db()

    register_routes(app)
    register_error_handlers(app)

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
