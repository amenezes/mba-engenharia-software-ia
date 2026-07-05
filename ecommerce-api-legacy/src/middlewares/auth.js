const { verifyToken } = require('../services/tokenService');

function extractToken(req) {
    const header = req.headers.authorization || '';
    return header.startsWith('Bearer ') ? header.slice(7) : null;
}

function verifyTokenMiddleware(req, res, next) {
    const token = extractToken(req);
    if (!token) return res.status(401).json({ erro: 'Token ausente' });
    const payload = verifyToken(token);
    if (!payload) return res.status(401).json({ erro: 'Token invalido' });
    req.user = payload;
    next();
}

function requireAdmin(req, res, next) {
    if (!req.user || req.user.role !== 'admin') {
        return res.status(403).json({ erro: 'Acesso restrito a administradores' });
    }
    next();
}

module.exports = {
    verifyToken: verifyTokenMiddleware,
    requireAdmin,
};
