from flask import Blueprint, jsonify, request
from sqlalchemy.orm import joinedload

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from config.constants import TASK_STATUS_VALIDOS, PRIORITY_MAX, PRIORITY_MIN, TITULO_MIN, TITULO_MAX

from datetime import datetime

task_bp = Blueprint('tasks', __name__)


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = (
        Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    )
    result = []
    for t in tasks:
        data = t.to_dict()
        data['overdue'] = t.is_overdue()
        data['user_name'] = t.user.name if t.user else None
        data['category_name'] = t.category.name if t.category else None
        result.append(data)
    return jsonify(result), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task nao encontrada'}), 404
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return jsonify(data), 200


@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados invalidos'}), 400

    title = data.get('title')
    if not title:
        return jsonify({'error': 'Titulo e obrigatorio'}), 400
    if len(title) < TITULO_MIN or len(title) > TITULO_MAX:
        return jsonify({'error': 'Titulo com tamanho invalido'}), 400

    status = data.get('status', 'pending')
    if status not in TASK_STATUS_VALIDOS:
        return jsonify({'error': 'Status invalido'}), 400

    priority = data.get('priority', 3)
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400

    user_id = data.get('user_id')
    if user_id and not db.session.get(User, user_id):
        return jsonify({'error': 'Usuario nao encontrado'}), 404

    category_id = data.get('category_id')
    if category_id and not db.session.get(Category, category_id):
        return jsonify({'error': 'Categoria nao encontrada'}), 404

    task = Task(
        title=title,
        description=data.get('description', ''),
        status=status,
        priority=priority,
        user_id=user_id,
        category_id=category_id,
    )

    due_date = data.get('due_date')
    if due_date:
        try:
            task.due_date = datetime.strptime(due_date, '%Y-%m-%d')
        except ValueError:
            return jsonify({'error': 'Formato de data invalido. Use YYYY-MM-DD'}), 400

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task nao encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados invalidos'}), 400

    if 'title' in data:
        if len(data['title']) < TITULO_MIN or len(data['title']) > TITULO_MAX:
            return jsonify({'error': 'Titulo com tamanho invalido'}), 400
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        if data['status'] not in TASK_STATUS_VALIDOS:
            return jsonify({'error': 'Status invalido'}), 400
        task.status = data['status']
    if 'priority' in data:
        if data['priority'] < PRIORITY_MIN or data['priority'] > PRIORITY_MAX:
            return jsonify({'error': 'Prioridade deve ser entre 1 e 5'}), 400
        task.priority = data['priority']
    if 'user_id' in data:
        if data['user_id'] and not db.session.get(User, data['user_id']):
            return jsonify({'error': 'Usuario nao encontrado'}), 404
        task.user_id = data['user_id']
    if 'category_id' in data:
        if data['category_id'] and not db.session.get(Category, data['category_id']):
            return jsonify({'error': 'Categoria nao encontrada'}), 404
        task.category_id = data['category_id']
    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], '%Y-%m-%d')
            except ValueError:
                return jsonify({'error': 'Formato de data invalido'}), 400
        else:
            task.due_date = None
    if 'tags' in data:
        task.tags = ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']

    task.updated_at = datetime.utcnow()
    db.session.commit()
    return jsonify(task.to_dict()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task nao encontrada'}), 404
    db.session.delete(task)
    db.session.commit()
    return jsonify({'message': 'Task deletada com sucesso'}), 200


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    tasks = Task.query
    if query:
        tasks = tasks.filter(
            db.or_(Task.title.ilike(f'%{query}%'), Task.description.ilike(f'%{query}%'))
        )
    if status:
        tasks = tasks.filter(Task.status == status)
    if priority:
        tasks = tasks.filter(Task.priority == int(priority))
    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    return jsonify([t.to_dict() for t in tasks.all()]), 200


@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    total = Task.query.count()
    done = Task.query.filter_by(status='done').count()
    overdue = (
        Task.query.filter(Task.due_date < datetime.utcnow())
        .filter(Task.status.notin_(['done', 'cancelled']))
        .count()
    )
    by_status = dict(
        db.session.query(Task.status, db.func.count(Task.id)).group_by(Task.status).all()
    )
    stats = {
        'total': total,
        'pending': by_status.get('pending', 0),
        'in_progress': by_status.get('in_progress', 0),
        'done': done,
        'cancelled': by_status.get('cancelled', 0),
        'overdue': overdue,
        'completion_rate': round((done / total) * 100, 2) if total > 0 else 0,
    }
    return jsonify(stats), 200
