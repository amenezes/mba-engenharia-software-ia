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
    let user = await findByEmail(email);
    if (!user) {
        const { lastID } = await create(name, email, require('../services/passwordService').hashPassword(pwd));
        user = await db.get('SELECT * FROM users WHERE id = ?', [lastID]);
    }
    return toSafeUser(user);
}

module.exports = { toSafeUser, findByEmail, findById, create, authenticate };
