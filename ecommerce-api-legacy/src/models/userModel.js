const db = require('../db');
const { verifyPassword } = require('../services/passwordService');

function toSafeUser(u) {
    if (!u) return null;
    const { pass, ...safe } = u;
    return safe;
}

function findByEmail(email) {
    return db.get('SELECT * FROM users WHERE email = ?', [email]);
}

function findById(id) {
    return db.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
}

function create(name, email, passwordHash) {
    return db.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)',
        [name, email, passwordHash]);
}

async function authenticate(name, email, pwd) {
    const user = await findByEmail(email);
    if (!user) return null;
    const ok = await verifyPassword(pwd, user.pass);
    return ok ? toSafeUser(user) : null;
}

module.exports = { toSafeUser, findByEmail, findById, create, authenticate };
