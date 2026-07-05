import logging

from flask import Flask, jsonify

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask):
    @app.errorhandler(404)
    def nao_encontrado(err):
        return jsonify({'error': 'Recurso nao encontrado'}), 404

    @app.errorhandler(400)
    def requisicao_invalida(err):
        return jsonify({'error': 'Requisicao invalida'}), 400

    @app.errorhandler(401)
    def nao_autorizado(err):
        return jsonify({'error': 'Nao autorizado'}), 401

    @app.errorhandler(Exception)
    def erro_inesperado(err):
        logger.exception("Erro nao tratado")
        return jsonify({'error': 'Erro interno do servidor'}), 500
