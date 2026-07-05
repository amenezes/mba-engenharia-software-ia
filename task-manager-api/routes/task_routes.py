from flask import Blueprint, jsonify, request

from database import db
from models.task import Task
from services import task_service
from middlewares.auth import login_required

from datetime import datetime

task_bp = Blueprint('tasks', __name__)


def _service_error(err):
    return jsonify({'error': err.message}), err.status


@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    return jsonify(task_service.list_tasks()), 200


@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    try:
        return jsonify(task_service.get_task(task_id)), 200
    except task_service.ValidationError as err:
        return _service_error(err)


@task_bp.route('/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    try:
        created = task_service.create_task(data)
        return jsonify(created), 201
    except task_service.ValidationError as err:
        return _service_error(err)


@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    data = request.get_json()
    try:
        updated = task_service.update_task(task_id, data)
        return jsonify(updated), 200
    except task_service.ValidationError as err:
        return _service_error(err)


@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    try:
        task_service.delete_task(task_id)
        return jsonify({'message': 'Task deletada com sucesso'}), 200
    except task_service.ValidationError as err:
        return _service_error(err)


@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    result = task_service.search_tasks(
        query=request.args.get('q', ''),
        status=request.args.get('status', ''),
        priority=request.args.get('priority', ''),
        user_id=request.args.get('user_id', ''),
    )
    return jsonify(result), 200


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
