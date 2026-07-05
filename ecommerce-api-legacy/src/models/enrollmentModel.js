const db = require('../db');

function createEnrollment(userId, courseId) {
    return db.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
}

function createPayment(enrollmentId, amount, status) {
    return db.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status]);
}

function createAuditLog(action) {
    return db.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
}

function deleteByUserId(userId) {
    return db.run('DELETE FROM users WHERE id = ?', [userId]);
}

// Relatorio em um unico SELECT com JOIN (resolve N+1).
function getFinancialReport() {
    return db.all(`
        SELECT c.title AS course,
               COALESCE(SUM(CASE WHEN p.status = 'PAID' THEN p.amount ELSE 0 END), 0) AS revenue,
               COUNT(e.id) AS enrollment_count
        FROM courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        LEFT JOIN payments p ON p.enrollment_id = e.id
        GROUP BY c.id
        ORDER BY c.title
    `);
}

module.exports = {
    createEnrollment,
    createPayment,
    createAuditLog,
    deleteByUserId,
    getFinancialReport,
};
