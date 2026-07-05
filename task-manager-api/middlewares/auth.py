from functools import wraps

import jwt
from flask import current_app, jsonify, request


def _extrair_token():
    header = request.headers.get('Authorization', '')
    if header.startswith('Bearer '):
        return header[7:]
    return None


def login_required(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        token = _extrair_token()
        if not token:
            return jsonify({'error': 'Token ausente'}), 401
        try:
            payload = jwt.decode(
                token, current_app.config['SECRET_KEY'], algorithms=['HS256']
            )
        except jwt.PyJWTError:
            return jsonify({'error': 'Token invalido'}), 401
        request.current_user = payload
        return f(*args, **kwargs)

    return decorado
