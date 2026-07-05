from flask import jsonify, request

from config.constants import (
    CATEGORIAS_VALIDAS,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
)
import models.produto_model as produto_model
from services.pedido_service import PedidoError


def _validar_produto(dados):
    if not dados:
        return None, ("Dados inválidos", 400)
    for campo in ("nome", "preco", "estoque"):
        if campo not in dados:
            return None, (f"{campo.capitalize()} é obrigatório", 400)
    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", "geral")
    descricao = dados.get("descricao", "")
    if preco < 0:
        return None, ("Preço não pode ser negativo", 400)
    if estoque < 0:
        return None, ("Estoque não pode ser negativo", 400)
    if len(nome) < NOME_PRODUTO_MIN or len(nome) > NOME_PRODUTO_MAX:
        return None, ("Nome com tamanho inválido", 400)
    if categoria not in CATEGORAS_VALIDAS:
        return None, ("Categoria inválida", 400)
    return (nome, descricao, preco, estoque, categoria), None


def listar():
    produtos = produto_model.get_todos()
    return jsonify({"dados": produtos, "sucesso": True}), 200


def buscar_por_id(produto_id):
    produto = produto_model.get_por_id(produto_id)
    if not produto:
        return jsonify({"erro": "Produto não encontrado", "sucesso": False}), 404
    return jsonify({"dados": produto, "sucesso": True}), 200


def criar():
    dados = request.get_json()
    validos, erro = _validar_produto(dados)
    if erro:
        return jsonify({"erro": erro[0]}), erro[1]
    novo_id = produto_model.criar(*validos)
    return (
        jsonify({"dados": {"id": novo_id}, "sucesso": True, "mensagem": "Produto criado"}),
        201,
    )


def atualizar(produto_id):
    if not produto_model.get_por_id(produto_id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    dados = request.get_json()
    validos, erro = _validar_produto(dados)
    if erro:
        return jsonify({"erro": erro[0]}), erro[1]
    produto_model.atualizar(produto_id, *validos)
    return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200


def deletar(produto_id):
    if not produto_model.get_por_id(produto_id):
        return jsonify({"erro": "Produto não encontrado"}), 404
    produto_model.deletar(produto_id)
    return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200


def buscar():
    termo = request.args.get("q", "")
    categoria = request.args.get("categoria") or None
    preco_min = request.args.get("preco_min")
    preco_max = request.args.get("preco_max")
    preco_min = float(preco_min) if preco_min else None
    preco_max = float(preco_max) if preco_max else None
    resultados = produto_model.buscar(termo, categoria, preco_min, preco_max)
    return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200
