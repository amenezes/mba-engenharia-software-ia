from werkzeug.security import check_password_hash, generate_password_hash

from database import get_db


def _to_dict(row):
    # senha intencionalmente omitida (anti-pattern #3)
    return {
        "id": row["id"],
        "nome": row["nome"],
        "email": row["email"],
        "tipo": row["tipo"],
        "criado_em": row["criado_em"],
    }


def get_todos():
    db = get_db()
    rows = db.execute("SELECT * FROM usuarios").fetchall()
    return [_to_dict(r) for r in rows]


def get_por_id(usuario_id):
    db = get_db()
    row = db.execute(
        "SELECT * FROM usuarios WHERE id = ?", (usuario_id,)
    ).fetchone()
    return _to_dict(row) if row else None


def criar(nome, email, senha, tipo="cliente"):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, generate_password_hash(senha), tipo),
    )
    db.commit()
    return cursor.lastrowid


def autenticar(email, senha):
    db = get_db()
    row = db.execute(
        "SELECT * FROM usuarios WHERE email = ?", (email,)
    ).fetchone()
    if row and check_password_hash(row["senha"], senha):
        return _to_dict(row)
    return None
