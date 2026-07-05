const { APPROVED_CARD_PREFIXES, PAYMENT_STATUS } = require('../constants');

class PaymentError extends Error {
    constructor(message) {
        super(message);
        this.status = 400;
    }
}

// Fake gateway: apro cartoes cujo BIN esta na lista (extraido da logica inline).
// Em producao, chamar um provider real (Stripe, etc.) com tokenizacao.
function charge(cardNumber, amount) {
    const approved = APPROVED_CARD_PREFIXES.some(prefix => cardNumber.startsWith(prefix));
    const status = approved ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
    if (status === PAYMENT_STATUS.DENIED) {
        throw new PaymentError('Pagamento recusado');
    }
    return { status, amount };
}

module.exports = { charge, PaymentError };
