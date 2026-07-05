from flask import Blueprint, jsonify

from controllers import pedido_controller

pedido_bp = Blueprint("pedidos", __name__)

pedido_bp.add_url_rule(
    "/pedidos", "criar", pedido_controller.criar, methods=["POST"]
)
pedido_bp.add_url_rule(
    "/pedidos", "listar_todos", pedido_controller.listar_todos, methods=["GET"]
)
pedido_bp.add_url_rule(
    "/pedidos/usuario/<int:usuario_id>",
    "listar_por_usuario",
    pedido_controller.listar_por_usuario,
    methods=["GET"],
)
pedido_bp.add_url_rule(
    "/pedidos/<int:pedido_id>/status",
    "atualizar_status",
    pedido_controller.atualizar_status,
    methods=["PUT"],
)
pedido_bp.add_url_rule(
    "/relatorios/vendas",
    "relatorio_vendas",
    pedido_controller.relatorio_vendas,
    methods=["GET"],
)
pedido_bp.add_url_rule(
    "/health", "health_check", pedido_controller.health_check, methods=["GET"]
)
pedido_bp.add_url_rule("/", "index", lambda: jsonify({
    "mensagem": "Bem-vindo a API da Loja",
    "versao": "2.0.0",
    "arquitetura": "MVC",
    "endpoints": {
        "produtos": "/produtos",
        "usuarios": "/usuarios",
        "pedidos": "/pedidos",
        "login": "/login",
        "relatorios": "/relatorios/vendas",
        "health": "/health",
    },
}))
