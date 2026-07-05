const crypto = require('crypto');
const config = require('../config');

function signToken(payload) {
    const body = Buffer.from(JSON.stringify({
        ...payload,
        exp: Date.now() + config.jwtExpirationHours * 3600 * 1000,
    })).toString('base64url');
    const sig = crypto.createHmac('sha256', config.jwtSecret).update(body).digest('base64url');
    return `${body}.${sig}`;
}

function verifyToken(token) {
    if (!token || !token.includes('.')) return null;
    const [body, sig] = token.split('.');
    const expected = crypto.createHmac('sha256', config.jwtSecret).update(body).digest('base64url');
    if (sig !== expected) return null;
    try {
        const payload = JSON.parse(Buffer.from(body, 'base64url').toString('utf8'));
        if (payload.exp && Date.now() > payload.exp) return null;
        return payload;
    } catch {
        return null;
    }
}

module.exports = { signToken, verifyToken };
