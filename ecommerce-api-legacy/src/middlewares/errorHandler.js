const config = require('../config');

class AppError extends Error {
    constructor(message, status = 500) {
        super(message);
        this.status = status;
    }
}

// eslint-disable-next-line no-unused-vars
function errorHandler(err, req, res, next) {
    const status = err.status || 500;
    if (status >= 500) {
        // Log estruturado (sem PAN/secrets).
        console.error(`[${new Date().toISOString()}] ${err.message}`);
    }
    res.status(status).json({
        erro: config.isProd && status >= 500 ? 'Erro interno do servidor' : err.message,
    });
}

function notFound(req, res) {
    res.status(404).json({ erro: 'Recurso não encontrado' });
}

module.exports = { errorHandler, notFound, AppError };
