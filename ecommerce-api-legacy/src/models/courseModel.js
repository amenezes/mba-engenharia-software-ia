const db = require('../db');

function findActiveById(id) {
    return db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
}

function listAll() {
    return db.all('SELECT id, title, price, active FROM courses');
}

module.exports = { findActiveById, listAll };
