from database import get_db

_PEDIDO_SELECT_JOIN = """
    SELECT p.id AS pedido_id, p.usuario_id, p.status, p.total, p.criado_em,
           ip.produto_id, ip.quantidade, ip.preco_unitario,
           pr.nome AS produto_nome
    FROM pedidos p
    LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
    LEFT JOIN produtos pr ON pr.id = ip.produto_id
"""


def _agrupar(rows):
    pedidos = {}
    for r in rows:
        pid = r["pedido_id"]
        if pid not in pedidos:
            pedidos[pid] = {
                "id": pid,
                "usuario_id": r["usuario_id"],
                "status": r["status"],
                "total": r["total"],
                "criado_em": r["criado_em"],
                "itens": [],
            }
        if r["produto_id"] is not None:
            pedidos[pid]["itens"].append({
                "produto_id": r["produto_id"],
                "produto_nome": r["produto_nome"] or "Desconhecido",
                "quantidade": r["quantidade"],
                "preco_unitario": r["preco_unitario"],
            })
    return list(pedidos.values())


def get_todos():
    db = get_db()
    rows = db.execute(_PEDIDO_SELECT_JOIN + " ORDER BY p.id").fetchall()
    return _agrupar(rows)


def get_por_usuario(usuario_id):
    db = get_db()
    rows = db.execute(
        _PEDIDO_SELECT_JOIN + " WHERE p.usuario_id = ? ORDER BY p.id",
        (usuario_id,),
    ).fetchall()
    return _agrupar(rows)


def criar(usuario_id, itens_com_preco, total):
    db = get_db()
    cursor = db.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cursor.lastrowid
    for item in itens_com_preco:
        db.execute(
            "INSERT INTO itens_pedido "
            "(pedido_id, produto_id, quantidade, preco_unitario) "
            "VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], item["preco_unitario"]),
        )
    db.commit()
    return pedido_id


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    db.execute(
        "UPDATE pedidos SET status = ? WHERE id = ?",
        (novo_status, pedido_id),
    )
    db.commit()
    return True


def relatorio():
    db = get_db()
    total_pedidos = db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0]
    faturamento = db.execute("SELECT SUM(total) FROM pedidos").fetchone()[0] or 0
    pendentes = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("pendente",)
    ).fetchone()[0]
    aprovados = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("aprovado",)
    ).fetchone()[0]
    cancelados = db.execute(
        "SELECT COUNT(*) FROM pedidos WHERE status = ?", ("cancelado",)
    ).fetchone()[0]
    return {
        "total_pedidos": total_pedidos,
        "faturamento_bruto": round(faturamento, 2),
        "pedidos_pendentes": pendentes,
        "pedidos_aprovados": aprovados,
        "pedidos_cancelados": cancelados,
    }


def contar_todas_tabelas():
    db = get_db()
    return {
        "produtos": db.execute("SELECT COUNT(*) FROM produtos").fetchone()[0],
        "usuarios": db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0],
        "pedidos": db.execute("SELECT COUNT(*) FROM pedidos").fetchone()[0],
    }
