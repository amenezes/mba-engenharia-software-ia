from flask import jsonify, request

from config.constants import STATUS_PEDIDO_VALIDOS
import models.pedido_model as pedido_model
from services import notificacao_service, pedido_service, relatorio_service


def criar():
    dados = request.get_json()
    if not dados:
        return jsonify({"erro": "Dados invalidos"}), 400
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        return jsonify({"erro": "Usuario ID e obrigatorio"}), 400
    if not itens:
        return jsonify({"erro": "Pedido deve ter pelo menos 1 item"}), 400
    try:
        resultado = pedido_service.processar_checkout(usuario_id, itens)
    except pedido_service.PedidoError as e:
        return jsonify({"erro": str(e), "sucesso": False}), 400
    notificacao_service.notificar_novo_pedido(resultado["pedido_id"], usuario_id)
    return (
        jsonify({"dados": resultado, "sucesso": True, "mensagem": "Pedido criado com sucesso"}),
        201,
    )


def listar_todos():
    pedidos = pedido_model.get_todos()
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def listar_por_usuario(usuario_id):
    pedidos = pedido_model.get_por_usuario(usuario_id)
    return jsonify({"dados": pedidos, "sucesso": True}), 200


def atualizar_status(pedido_id):
    dados = request.get_json() or {}
    novo_status = dados.get("status", "")
    if novo_status not in STATUS_PEDIDO_VALIDOS:
        return jsonify({"erro": "Status invalido"}), 400
    pedido_model.atualizar_status(pedido_id, novo_status)
    notificacao_service.notificar_status_pedido(pedido_id, novo_status)
    return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200


def relatorio_vendas():
    relatorio = relatorio_service.gerar()
    return jsonify({"dados": relatorio, "sucesso": True}), 200


def health_check():
    counts = pedido_model.contar_todas_tabelas()
    return (
        jsonify(
            {
                "status": "ok",
                "database": "connected",
                "counts": counts,
                "versao": "2.0.0",
                "ambiente": "producao",
            }
        ),
        200,
    )
