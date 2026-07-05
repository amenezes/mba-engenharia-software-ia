from config.constants import (
    FAIXA_DESCONTO_ALTO,
    FAIXA_DESCONTO_BAIXO,
    FAIXA_DESCONTO_MEDIO,
    TAXA_DESCONTO_ALTO,
    TAXA_DESCONTO_BAIXO,
    TAXA_DESCONTO_MEDIO,
)
import models.pedido_model as pedido_model


def calcular_desconto_aplicavel(faturamento):
    if faturamento > FAIXA_DESCONTO_ALTO:
        return faturamento * TAXA_DESCONTO_ALTO
    if faturamento > FAIXA_DESCONTO_MEDIO:
        return faturamento * TAXA_DESCONTO_MEDIO
    if faturamento > FAIXA_DESCONTO_BAIXO:
        return faturamento * TAXA_DESCONTO_BAIXO
    return 0


def gerar():
    base = pedido_model.relatorio()
    faturamento = base["faturamento_bruto"]
    desconto = calcular_desconto_aplicavel(faturamento)
    base.update(
        {
            "desconto_aplicavel": round(desconto, 2),
            "faturamento_liquido": round(faturamento - desconto, 2),
            "ticket_medio": round(faturamento / base["total_pedidos"], 2)
            if base["total_pedidos"] > 0
            else 0,
        }
    )
    return base
