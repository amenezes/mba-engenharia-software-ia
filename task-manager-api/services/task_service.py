from datetime import datetime

from database import db
from models.task import Task
from models.user import User
from models.category import Category
from config.constants import (
    TASK_STATUS_VALIDOS,
    PRIORITY_MIN,
    PRIORITY_MAX,
    TITULO_MIN,
    TITULO_MAX,
)

DATE_FORMAT = '%Y-%m-%d'


class ValidationError(Exception):
    def __init__(self, message, status=400):
        super().__init__(message)
        self.message = message
        self.status = status


def list_tasks():
    from sqlalchemy.orm import joinedload

    tasks = Task.query.options(joinedload(Task.user), joinedload(Task.category)).all()
    result = []
    for t in tasks:
        data = t.to_dict()
        data['overdue'] = t.is_overdue()
        data['user_name'] = t.user.name if t.user else None
        data['category_name'] = t.category.name if t.category else None
        result.append(data)
    return result


def get_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise ValidationError('Task não encontrada', 404)
    data = task.to_dict()
    data['overdue'] = task.is_overdue()
    return data


def _resolve_references(user_id, category_id):
    if user_id and not db.session.get(User, user_id):
        raise ValidationError('Usuário não encontrado', 404)
    if category_id and not db.session.get(Category, category_id):
        raise ValidationError('Categoria não encontrada', 404)


def _validate_task_fields(title, status, priority):
    if not title:
        raise ValidationError('Título é obrigatório')
    if len(title) < TITULO_MIN or len(title) > TITULO_MAX:
        raise ValidationError('Título com tamanho inválido')
    if status not in TASK_STATUS_VALIDOS:
        raise ValidationError('Status inválido')
    if priority < PRIORITY_MIN or priority > PRIORITY_MAX:
        raise ValidationError('Prioridade deve ser entre 1 e 5')


def create_task(data):
    if not data:
        raise ValidationError('Dados inválidos')

    title = data.get('title')
    status = data.get('status', 'pending')
    priority = data.get('priority', 3)
    _validate_task_fields(title, status, priority)

    user_id = data.get('user_id')
    category_id = data.get('category_id')
    _resolve_references(user_id, category_id)

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
            task.due_date = datetime.strptime(due_date, DATE_FORMAT)
        except ValueError:
            raise ValidationError('Formato de data inválido. Use YYYY-MM-DD')

    tags = data.get('tags')
    if tags:
        task.tags = ','.join(tags) if isinstance(tags, list) else tags

    db.session.add(task)
    db.session.commit()
    return task.to_dict()


def update_task(task_id, data):
    task = db.session.get(Task, task_id)
    if not task:
        raise ValidationError('Task não encontrada', 404)
    if not data:
        raise ValidationError('Dados inválidos')

    if 'title' in data:
        if len(data['title']) < TITULO_MIN or len(data['title']) > TITULO_MAX:
            raise ValidationError('Título com tamanho inválido')
        task.title = data['title']
    if 'description' in data:
        task.description = data['description']
    if 'status' in data:
        if data['status'] not in TASK_STATUS_VALIDOS:
            raise ValidationError('Status inválido')
        task.status = data['status']
    if 'priority' in data:
        if data['priority'] < PRIORITY_MIN or data['priority'] > PRIORITY_MAX:
            raise ValidationError('Prioridade deve ser entre 1 e 5')
        task.priority = data['priority']
    if 'user_id' in data:
        if data['user_id'] and not db.session.get(User, data['user_id']):
            raise ValidationError('Usuário não encontrado', 404)
        task.user_id = data['user_id']
    if 'category_id' in data:
        if data['category_id'] and not db.session.get(Category, data['category_id']):
            raise ValidationError('Categoria não encontrada', 404)
        task.category_id = data['category_id']
    if 'due_date' in data:
        if data['due_date']:
            try:
                task.due_date = datetime.strptime(data['due_date'], DATE_FORMAT)
            except ValueError:
                raise ValidationError('Formato de data inválido')
        else:
            task.due_date = None
    if 'tags' in data:
        task.tags = (
            ','.join(data['tags']) if isinstance(data['tags'], list) else data['tags']
        )

    task.updated_at = datetime.utcnow()
    db.session.commit()
    return task.to_dict()


def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        raise ValidationError('Task não encontrada', 404)
    db.session.delete(task)
    db.session.commit()
    return task_id


def search_tasks(query, status, priority, user_id):
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
    return [t.to_dict() for t in tasks.all()]
