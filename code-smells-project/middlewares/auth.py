from functools import wraps

import jwt
from flask import current_app, jsonify, request


def _extrair_token():
    header = request.headers.get("Authorization", "")
    if header.startswith("Bearer "):
        return header[7:]
    return None


def _decodificar(token):
    return jwt.decode(token, current_app.config["SECRET_KEY"], algorithms=["HS256"])


def login_required(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        token = _extrair_token()
        if not token:
            return jsonify({"erro": "Token ausente"}), 401
        try:
            payload = _decodificar(token)
        except jwt.PyJWTError:
            return jsonify({"erro": "Token inválido"}), 401
        request.current_user = payload
        return f(*args, **kwargs)

    return decorado


def admin_required(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        token = _extrair_token()
        if not token:
            return jsonify({"erro": "Token ausente"}), 401
        try:
            payload = _decodificar(token)
        except jwt.PyJWTError:
            return jsonify({"erro": "Token inválido"}), 401
        if payload.get("tipo") != "admin":
            return jsonify({"erro": "Acesso restrito a administradores"}), 403
        request.current_user = payload
        return f(*args, **kwargs)

    return decorado
