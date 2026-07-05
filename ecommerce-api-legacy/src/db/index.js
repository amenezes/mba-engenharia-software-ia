const sqlite3 = require('sqlite3');
const { hashPassword } = require('../services/passwordService');
const config = require('../config');

const db = new sqlite3.Database(':memory:');

function run(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function (err) {
            if (err) reject(err);
            else resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) reject(err);
            else resolve(row);
        });
    });
}

function all(sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) reject(err);
            else resolve(rows);
        });
    });
}

const SCHEMA = `
CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT);
CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
CREATE TABLE IF NOT EXISTS enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER);
CREATE TABLE IF NOT EXISTS payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT);
CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

async function initDb() {
    db.serialize();
    for (const stmt of SCHEMA.trim().split(';').filter(s => s.trim())) {
        await run(stmt);
    }
    await run("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)",
        ['Leonan', 'leonan@fullcycle.com.br', hashPassword(config.seedUserPassword)]);
    await run("INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)",
        ['Clean Architecture', 997.00, 'Docker', 497.00]);
    await run("INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)");
    await run("INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')");
}

module.exports = { db, run, get, all, initDb };
