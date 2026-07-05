import logging

from database import get_db
import models.pedido_model as pedido_model
import models.produto_model as produto_model

logger = logging.getLogger(__name__)


class PedidoError(Exception):
    pass


def processar_checkout(usuario_id, itens):
    if not itens:
        raise PedidoError("Pedido deve ter pelo menos 1 item")

    produto_ids = [i["produto_id"] for i in itens]
    produtos = produto_model.get_por_ids(produto_ids)

    itens_com_preco = []
    total = 0
    for item in itens:
        produto = produtos.get(item["produto_id"])
        if produto is None:
            raise PedidoError(f"Produto {item['produto_id']} não encontrado")
        quantidade = item["quantidade"]
        if produto["estoque"] < quantidade:
            raise PedidoError(f"Estoque insuficiente para {produto['nome']}")
        preco_unit = produto["preco"]
        itens_com_preco.append(
            {
                "produto_id": item["produto_id"],
                "quantidade": quantidade,
                "preco_unitario": preco_unit,
            }
        )
        total += preco_unit * quantidade

    db = get_db()
    try:
        pedido_id = pedido_model.criar(usuario_id, itens_com_preco, total)
        for item in itens_com_preco:
            produto_model.baixar_estoque(item["produto_id"], item["quantidade"])
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {"pedido_id": pedido_id, "total": round(total, 2)}
