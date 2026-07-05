import logging

logger = logging.getLogger(__name__)


def notificar_novo_pedido(pedido_id, usuario_id):
    logger.info("EMAIL: pedido %s criado para usuario %s", pedido_id, usuario_id)
    logger.info("SMS: seu pedido %s foi recebido", pedido_id)
    logger.info("PUSH: novo pedido %s recebido pelo sistema", pedido_id)


def notificar_status_pedido(pedido_id, novo_status):
    if novo_status == "aprovado":
        logger.info("Pedido %s aprovado — preparar envio", pedido_id)
    elif novo_status == "cancelado":
        logger.info("Pedido %s cancelado — devolver estoque", pedido_id)
