// Constantes de dominio (substitui magic numbers/strings).
const PAYMENT_STATUS = Object.freeze({
    PAID: 'PAID',
    DENIED: 'DENIED',
    PENDING: 'PENDING',
});

// BINs que aprovam no fake gateway (apenas para o servico de pagamento).
const APPROVED_CARD_PREFIXES = Object.freeze(['4']);

module.exports = { PAYMENT_STATUS, APPROVED_CARD_PREFIXES };
