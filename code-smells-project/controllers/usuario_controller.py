import datetime

import jwt
from flask import current_app, jsonify, request

import models.usuario_model as usuario_model
from config.settings import Config


def _gerar_token(usuario):
    expira = datetime.datetime.utcnow() + datetime.timedelta(
        hours=Config.JWT_EXPIRATION_HOURS
    )
    payload = {"sub": usuario["id"], "nome": usuario["nome"], "tipo": usuario["tipo"], "exp": expira}
    return jwt.encode(payload, current_app.config["SECRET_KEY"], algorithm="HS256")


def listar():
    usuarios = usuario_model.get_todos()
    return jsonify({"dados": usuarios, "sucesso": True}), 200


def buscar_por_id(usuario_id):
    usuario = usuario_model.get_por_id(usuario_id)
    if not usuario:
        return jsonify({"erro": "Usuario nao encontrado"}), 404
    return jsonify({"dados": usuario, "sucesso": True}), 200


def criar():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados invalidos"}), 400
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not nome or not email or not senha:
        return jsonify({"erro": "Nome, email e senha sao obrigatorios"}), 400
    novo_id = usuario_model.criar(nome, email, senha)
    return jsonify({"dados": {"id": novo_id}, "sucesso": True}), 201


def login():
    dados = request.get_json() or {}
    email = dados.get("email", "")
    senha = dados.get("senha", "")
    if not email or not senha:
        return jsonify({"erro": "Email e senha sao obrigatorios"}), 400
    usuario = usuario_model.autenticar(email, senha)
    if not usuario:
        return jsonify({"erro": "Email ou senha invalidos", "sucesso": False}), 401
    token = _gerar_token(usuario)
    return (
        jsonify(
            {
                "dados": usuario,
                "token": token,
                "sucesso": True,
                "mensagem": "Login OK",
            }
        ),
        200,
    )
