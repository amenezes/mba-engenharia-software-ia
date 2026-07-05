import logging

from flask import Flask, jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask):
    @app.errorhandler(404)
    def nao_encontrado(err):
        return jsonify({"erro": "Recurso não encontrado"}), 404

    @app.errorhandler(400)
    def requisicao_invalida(err):
        return jsonify({"erro": "Requisição inválida"}), 400

    @app.errorhandler(401)
    def nao_autorizado(err):
        return jsonify({"erro": "Não autorizado"}), 401

    @app.errorhandler(405)
    def metodo_nao_permitido(err):
        return jsonify({"erro": "Método não permitido"}), 405

    @app.errorhandler(Exception)
    def erro_inesperado(err):
        logger.exception("Erro não tratado")
        return jsonify({"erro": "Erro interno do servidor"}), 500
