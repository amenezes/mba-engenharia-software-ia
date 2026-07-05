from flask import Blueprint, current_app, jsonify, request
from datetime import datetime, timedelta
import jwt

from database import db
from models.user import User
from config.settings import Config
from services import user_service
from middlewares.auth import login_required

user_bp = Blueprint('users', __name__)


def _service_error(err):
    return jsonify({'error': err.message}), err.status


@user_bp.route('/users', methods=['GET'])
def get_users():
    return jsonify(user_service.list_users()), 200


@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        return jsonify(user_service.get_user(user_id)), 200
    except user_service.ValidationError as err:
        return _service_error(err)


@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    try:
        created = user_service.create_user(data)
        return jsonify(created), 201
    except user_service.ValidationError as err:
        return _service_error(err)


@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    data = request.get_json()
    try:
        updated = user_service.update_user(user_id, data)
        return jsonify(updated), 200
    except user_service.ValidationError as err:
        return _service_error(err)


@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
def delete_user(user_id):
    try:
        user_service.delete_user(user_id)
        return jsonify({'message': 'Usuário deletado com sucesso'}), 200
    except user_service.ValidationError as err:
        return _service_error(err)


@user_bp.route('/users/<int:user_id>/tasks', methods=['GET'])
def get_user_tasks(user_id):
    try:
        return jsonify(user_service.get_user_tasks(user_id)), 200
    except user_service.ValidationError as err:
        return _service_error(err)


@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email e senha são obrigatórios'}), 400

    try:
        user = user_service.authenticate(email, password)
    except user_service.ValidationError as err:
        return _service_error(err)

    if not user:
        return jsonify({'error': 'Credenciais inválidas'}), 401

    expira = datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
    token = jwt.encode(
        {'sub': user.id, 'name': user.name, 'role': user.role, 'exp': expira},
        current_app.config['SECRET_KEY'],
        algorithm='HS256',
    )

    return jsonify({
        'message': 'Login realizado com sucesso',
        'user': user.to_dict(),
        'token': token,
    }), 200
