from flask import Blueprint, jsonify, request

from database import get_db
from middlewares.auth import admin_required

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin/reset-db", methods=["POST"])
@admin_required
def reset_database():
    db = get_db()
    cursor = db.cursor()
    for tabela in ("itens_pedido", "pedidos", "produtos", "usuarios"):
        cursor.execute(f"DELETE FROM {tabela}")
    db.commit()
    return jsonify({"mensagem": "Banco de dados resetado", "sucesso": True}), 200


@admin_bp.route("/admin/query", methods=["POST"])
@admin_required
def executar_query():
    dados = request.get_json() or {}
    query = dados.get("sql", "")
    if not query:
        return jsonify({"erro": "Query nao informada"}), 400
    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            return jsonify({"dados": [dict(r) for r in rows], "sucesso": True}), 200
        db.commit()
        return jsonify({"mensagem": "Query executada", "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
