import re

from database import db
from models.user import User
from models.task import Task
from config.constants import USER_ROLES_VALIDOS

EMAIL_REGEX = r'^[a-zA-Z0-9+_.-]+@[a-zA-Z0-9.-]+$'
MIN_PASSWORD_LENGTH = 4


class ValidationError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def list_users():
    users = User.query.all()
    result = []
    for u in users:
        user_data = u.to_dict()
        user_data['task_count'] = len(u.tasks)
        result.append(user_data)
    return result


def get_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ValidationError('Usuário não encontrado', 404)
    data = user.to_dict()
    data['tasks'] = [t.to_dict() for t in Task.query.filter_by(user_id=user_id).all()]
    return data


def _validate_user_fields(name, email, password, role):
    if not name:
        raise ValidationError('Nome é obrigatório')
    if not email:
        raise ValidationError('Email é obrigatório')
    if not password:
        raise ValidationError('Senha é obrigatória')
    if not re.match(EMAIL_REGEX, email):
        raise ValidationError('Email inválido')
    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError('Senha deve ter no mínimo 4 caracteres')
    if role not in USER_ROLES_VALIDOS:
        raise ValidationError('Role inválido')


def create_user(data):
    if not data:
        raise ValidationError('Dados inválidos')

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    role = data.get('role', 'user')

    _validate_user_fields(name, email, password, role)

    if User.query.filter_by(email=email).first():
        raise ValidationError('Email já cadastrado', 409)

    user = User()
    user.name = name
    user.email = email
    user.set_password(password)
    user.role = role

    db.session.add(user)
    db.session.commit()
    return user.to_dict()


def update_user(user_id, data):
    user = db.session.get(User, user_id)
    if not user:
        raise ValidationError('Usuário não encontrado', 404)
    if not data:
        raise ValidationError('Dados inválidos')

    if 'name' in data:
        user.name = data['name']
    if 'email' in data:
        if not re.match(EMAIL_REGEX, data['email']):
            raise ValidationError('Email inválido')
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user_id:
            raise ValidationError('Email já cadastrado', 409)
        user.email = data['email']
    if 'password' in data:
        if len(data['password']) < MIN_PASSWORD_LENGTH:
            raise ValidationError('Senha muito curta')
        user.set_password(data['password'])
    if 'role' in data:
        if data['role'] not in USER_ROLES_VALIDOS:
            raise ValidationError('Role inválido')
        user.role = data['role']
    if 'active' in data:
        user.active = data['active']

    db.session.commit()
    return user.to_dict()


def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ValidationError('Usuário não encontrado', 404)
    for t in Task.query.filter_by(user_id=user_id).all():
        db.session.delete(t)
    db.session.delete(user)
    db.session.commit()
    return user_id


def get_user_tasks(user_id):
    user = db.session.get(User, user_id)
    if not user:
        raise ValidationError('Usuário não encontrado', 404)
    result = []
    for t in Task.query.filter_by(user_id=user_id).all():
        task_data = t.to_dict()
        task_data['overdue'] = t.is_overdue()
        result.append(task_data)
    return result


def authenticate(email, password):
    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return None
    if not user.active:
        raise ValidationError('Usuário inativo', 403)
    return user
