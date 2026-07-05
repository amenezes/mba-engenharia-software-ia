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

    # Apenas SELECT read-only: valida o prefixo ANTES de executar e bloqueia
    # stacking de statements (";") para evitar SQL arbitrario (DROP/DELETE/...).
    normalized = query.strip()
    if ";" in normalized.rstrip(";"):
        return jsonify({"erro": "Consultas multiplas nao sao permitidas"}), 403
    if not normalized.upper().startswith("SELECT"):
        return jsonify({"erro": "Apenas consultas SELECT sao permitidas"}), 403

    db = get_db()
    cursor = db.cursor()
    try:
        cursor.execute(normalized)
        rows = cursor.fetchall()
        return jsonify({"dados": [dict(r) for r in rows], "sucesso": True}), 200
    except Exception as e:
        return jsonify({"erro": str(e)}), 500
