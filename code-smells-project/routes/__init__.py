from flask import Flask

from routes.admin_routes import admin_bp
from routes.pedido_routes import pedido_bp
from routes.produto_routes import produto_bp
from routes.usuario_routes import usuario_bp


def register_routes(app: Flask):
    app.register_blueprint(produto_bp)
    app.register_blueprint(usuario_bp)
    app.register_blueprint(pedido_bp)
    app.register_blueprint(admin_bp)
